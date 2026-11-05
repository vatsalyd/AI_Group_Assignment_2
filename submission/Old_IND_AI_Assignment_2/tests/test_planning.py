import collections
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'problem2'))
from lower_bound import RoverLowerBound
from run_planner import load_task, simulate_independently


class PlanningTests(unittest.TestCase):
    def test_saved_plans_with_two_simulators(self):
        for scenario, filename in [('original', 'Problem.pddl'), ('extended', 'Problem_extended.pddl')]:
            full = load_task(ROOT / 'problem2' / filename, optimized=False)
            operators = {op.name: op for op in full.operators}
            heuristic = RoverLowerBound(full.initial_state)
            for search in ('gbfs', 'astar'):
                prefix = ROOT / 'problem2' / 'outputs' / f'{scenario}_{search}'
                names = prefix.with_suffix('.plan').read_text().splitlines()
                final, _ = simulate_independently(full.initial_state, names, full.goals)
                state = full.initial_state
                for index, name in enumerate(names):
                    self.assertLessEqual(heuristic(SimpleNamespace(state=state)), len(names) - index)
                    self.assertTrue(operators[name].applicable(state))
                    state = operators[name].apply(state)
                self.assertEqual(set(state), final)
                self.assertTrue(full.goal_reached(state))
                self.assertEqual(heuristic(SimpleNamespace(state=state)), 0)
                metrics = json.loads(prefix.with_suffix('.json').read_text())
                self.assertEqual(metrics['plan_length'], len(names))

    def test_routes_capacity_and_drill(self):
        full = load_task(ROOT / 'problem2' / 'Problem_extended.pddl', optimized=False)
        initial = full.initial_state
        illegal = [
            ['(move curiosity base siteb)'],
            ['(move curiosity base sitea)', '(move curiosity sitea sitec)',
             '(move curiosity sitec sited)', '(move curiosity sited sitec)'],
            ['(move curiosity base sitea)', '(move curiosity sitea sitec)',
             '(collect-hard curiosity rock3 bay1 sitec)'],
            ['(move curiosity base sitea)', '(collect-soft curiosity rock1 bay1 sitea)',
             '(move curiosity sitea sitec)', '(move curiosity sitec sited)',
             '(collect-soft curiosity rock4 bay1 sited)'],
        ]
        for names in illegal:
            with self.assertRaises(AssertionError):
                simulate_independently(initial, names, full.goals)
        self.assertNotIn('(connected base siteb)', initial)
        self.assertNotIn('(connected siteb base)', initial)
        self.assertIn('(connected sitec sited)', initial)
        self.assertNotIn('(connected sited sitec)', initial)

    def test_lower_bound_consistency_on_reachable_states(self):
        for filename in ('Problem.pddl', 'Problem_extended.pddl'):
            full = load_task(ROOT / 'problem2' / filename, optimized=False)
            heuristic = RoverLowerBound(full.initial_state)
            queue = collections.deque([full.initial_state])
            seen = {full.initial_state}
            for _ in range(800):
                if not queue:
                    break
                state = queue.popleft()
                value = heuristic(SimpleNamespace(state=state))
                for _, successor in full.get_successor_states(state):
                    self.assertLessEqual(value, 1 + heuristic(SimpleNamespace(state=successor)))
                    if successor not in seen:
                        seen.add(successor)
                        queue.append(successor)


if __name__ == '__main__':
    unittest.main()
