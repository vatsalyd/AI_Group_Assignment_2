import argparse
import collections
import io
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'vendor'))


def load_task(problem_file, optimized=True):
    from pyperplan.pddl.parser import Parser
    from pyperplan.grounding import ground
    parser = Parser(str(ROOT / 'problem2' / 'Domain.pddl'), str(problem_file))
    domain = parser.parse_domain()
    problem = parser.parse_problem(domain)
    task = ground(problem, remove_statics_from_initial_state=optimized,
                  remove_irrelevant_operators=optimized)
    task.operators = sorted(task.operators, key=lambda op: op.name)
    return task


def check_invariants(state, rocks):
    facts = [fact.strip('()').split() for fact in state]
    rover_positions = [f for f in facts if f[0] == 'at']
    assert len(rover_positions) == 1, 'Rover must have exactly one location'
    for rock in rocks:
        positions = [f for f in facts if f[0] in ('rock-at', 'in-bay') and f[1] == rock]
        assert len(positions) == 1, f'{rock} must have exactly one location or bay'
    for bay in ('bay1', 'bay2'):
        contents = [f for f in facts if f[0] == 'in-bay' and f[2] == bay]
        assert len(contents) <= 1, 'Bay capacity exceeded'
        assert (f'(empty {bay})' in state) == (len(contents) == 0), 'Empty flag inconsistent'


def simulate_independently(initial, names, goals):
    state = set(initial)
    rocks = sorted(f.strip('()').split()[1] for f in state if f.startswith('(rock-at '))
    trace = []
    check_invariants(state, rocks)
    for step, name in enumerate(names, 1):
        action, *args = name.strip('()').split()
        if action == 'move':
            rover, origin, destination = args
            assert f'(at {rover} {origin})' in state
            assert f'(connected {origin} {destination})' in state
            state.remove(f'(at {rover} {origin})')
            state.add(f'(at {rover} {destination})')
        elif action == 'pick-drill':
            rover, drill, location = args
            assert f'(at {rover} {location})' in state
            assert f'(drill-at {drill} {location})' in state
            state.remove(f'(drill-at {drill} {location})')
            state.add(f'(has-drill {rover})')
        elif action in ('collect-soft', 'collect-hard'):
            rover, rock, bay, location = args
            kind = action.split('-')[1]
            assert f'(at {rover} {location})' in state
            assert f'(rock-at {rock} {location})' in state
            assert f'(bay-of {bay} {rover})' in state
            assert f'(empty {bay})' in state
            assert f'({kind} {rock})' in state
            if kind == 'hard':
                assert f'(has-drill {rover})' in state
            state.remove(f'(rock-at {rock} {location})')
            state.remove(f'(empty {bay})')
            state.add(f'(in-bay {rock} {bay})')
        elif action == 'deposit':
            rover, rock, bay, location = args
            assert f'(at {rover} {location})' in state
            assert f'(bay-of {bay} {rover})' in state
            assert f'(in-bay {rock} {bay})' in state
            state.remove(f'(in-bay {rock} {bay})')
            state.add(f'(empty {bay})')
            state.add(f'(rock-at {rock} {location})')
        else:
            raise ValueError(action)
        check_invariants(state, rocks)
        trace += [f'{step:02}. {name}', '    ' + '; '.join(sorted(
            f for f in state if f.startswith(('(at ', '(rock-at ', '(in-bay ', '(empty ', '(has-drill '))))]
    assert set(goals) <= state, 'Goal not reached'
    return state, trace


def run(scenario, search_name):
    from pyperplan.search import astar_search, greedy_best_first_search
    from pyperplan.heuristics.relaxation import hFFHeuristic, hMaxHeuristic
    source = ROOT / 'problem2' / ('Problem.pddl' if scenario == 'original' else 'Problem_extended.pddl')
    output = ROOT / 'problem2' / 'outputs'
    output.mkdir(exist_ok=True)
    capture = io.StringIO()
    handler = logging.StreamHandler(capture)
    logging.getLogger().handlers = [handler]
    logging.getLogger().setLevel(logging.INFO)
    start = time.perf_counter()
    task = load_task(source)
    search = greedy_best_first_search if search_name == 'gbfs' else astar_search
    heuristic = hFFHeuristic(task) if search_name == 'gbfs' else hMaxHeuristic(task)
    search_start = time.perf_counter()
    cpu_start = time.process_time()
    solution = search(task, heuristic)
    cpu_seconds = time.process_time() - cpu_start
    search_seconds = time.perf_counter() - search_start
    planning_seconds = time.perf_counter() - start
    if solution is None:
        raise RuntimeError('No solution found')
    names = [op.name for op in solution]
    full_task = load_task(source, optimized=False)
    operators = {op.name: op for op in full_task.operators}
    state = full_task.initial_state
    for name in names:
        op = operators[name]
        assert op.applicable(state), name
        state = op.apply(state)
    assert full_task.goal_reached(state)
    independent_state, trace = simulate_independently(full_task.initial_state, names, full_task.goals)
    assert set(state) == independent_state
    expansion_match = re.search(r'(\d+) Nodes expanded', capture.getvalue())
    assert expansion_match, 'Planner did not report expansions'
    import importlib.metadata
    metrics = {'scenario': scenario, 'search': search_name,
               'heuristic': 'hFF' if search_name == 'gbfs' else 'hMax',
               'planner': 'pyperplan', 'planner_version': importlib.metadata.version('pyperplan'),
               'plan_length': len(names), 'total_actions': len(names),
               'action_counts': dict(collections.Counter(name.split()[0][1:] for name in names)),
               'nodes_expanded_including_goal': int(expansion_match[1]),
               'search_wall_seconds': search_seconds, 'search_cpu_seconds': cpu_seconds,
               'planning_wall_seconds': planning_seconds,
               'grounded_operators': len(task.operators), 'validated': True,
               'goal_facts': sorted(full_task.goals),
               'final_dynamic_state': sorted(f for f in state if f.startswith(
                   ('(at ', '(rock-at ', '(in-bay ', '(empty ', '(has-drill ')))}
    prefix = output / f'{scenario}_{search_name}'
    prefix.with_suffix('.plan').write_text('\n'.join(names) + '\n', encoding='utf-8')
    prefix.with_suffix('.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    prefix.with_suffix('.trace.txt').write_text('\n'.join(trace) + '\n\nFINAL GOALS VERIFIED\n' +
                                              '\n'.join(metrics['final_dynamic_state']) + '\n', encoding='utf-8')
    log = capture.getvalue() + '\n' + json.dumps(metrics, indent=2) + '\n\nPLAN\n' + '\n'.join(
        f'{i:02}. {name}' for i, name in enumerate(names, 1)) + '\n\nFINAL GOALS VERIFIED\n' + '\n'.join(metrics['final_dynamic_state']) + '\n'
    prefix.with_suffix('.log').write_text(log, encoding='utf-8')
    print(log)


def main():
    if os.environ.get('PYTHONHASHSEED') != '0':
        environment = dict(os.environ, PYTHONHASHSEED='0')
        result = subprocess.run([sys.executable, __file__, *sys.argv[1:]], env=environment)
        raise SystemExit(result.returncode)
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=('original', 'extended'), required=True)
    parser.add_argument('--search', choices=('gbfs', 'astar'), required=True)
    args = parser.parse_args()
    run(args.scenario, args.search)


if __name__ == '__main__':
    main()
