import csv
from html import escape
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
sys.path.insert(0, str(ROOT / 'problem1'))
from bayesian_network import PARENTS, STATES, expert_model


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(map(str, headers)) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def csv_table(path):
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.reader(stream)
        headers = next(reader)
        rows = [[f'{float(v):.9f}' if '.' in v and v.replace('.', '', 1).isdigit() else v
                 for v in row] for row in reader]
    return table(headers, rows)


def problem1_report(results):
    model = expert_model()
    sections = ['''# Problem 1: Smart home energy consumption

## A. Expert network and inference

The network has edges D -> O, W -> A, O -> A, O -> L, A -> E,
and L -> E. Its factorization is

`P(W,D,O,A,L,E) = P(W) P(D) P(O|D) P(A|W,O) P(L|O) P(E|A,L)`.

W is Weather, D is DayType, O is Occupancy, A is AC usage, L is ApplianceLoad,
and E is EnergyConsumption. The state labels follow the assignment. The code
constructs each CPT explicitly, checks each parent configuration sums to one,
and checks the 96-row joint distribution sums to one. Inference sums compatible
joint probabilities and divides by the probability of the evidence.

![Expert Bayesian network](../problem1/outputs/network.png)

### Expert CPTs

Each row below lists probabilities in the stated state order.''']
    for node in model:
        sections += [f'**{node}**: states {", ".join(STATES[node])}; parents {", ".join(PARENTS[node]) or "none"}.\n\n' +
                     table(['Parent configuration', *STATES[node]],
                           [((', '.join(key) or 'prior'), *[f'{p:.4f}' for p in probs])
                            for key, probs in model[node].items()])]
    descriptions = ['P(E=High)', 'P(E=High given W=Hot)', 'P(E=High given D=Weekend)',
                    'P(E=High given W=Cold, O=High)', 'P(W=Hot given E=High)',
                    'P(A=On given E=High)', 'P(A=On given E=High, L=Heavy)']
    sections += ['### Query results\n\n' + table(['Query', 'Probability', 'Result'],
                 [(f'Q{i}', desc, f'{p:.10f}') for i, (desc, p) in enumerate(zip(descriptions, results['expert']), 1)]),
                 '''### Explaining away

Q6 is 0.6928666813 and Q7 is 0.6498993030. Observing high consumption makes
heavy AC use more likely. Once heavy appliance load is known, it provides
another explanation for high consumption, so the posterior probability of
AC use decreases. A and L also share the ancestor O; they are not marginally
independent causes. The numerical comparison still shows the explaining-away
effect requested in the assignment.

### Q1 by hand

Sum out the five other variables:

`P(E=High) = sum_w sum_d sum_o sum_a sum_l P(w)P(d)P(o|d)P(a|w,o)P(l|o)P(E=High|a,l)`.

First, `P(O=High) = 0.70*0.45 + 0.30*0.80 = 0.555`, so `P(O=Low)=0.445`.
W is independent of O because the unconditioned paths between them contain
colliders. For fixed w,o, write a=P(A=On|w,o) and l=P(L=Heavy|o).
Then summing the four A,L configurations gives

`g(w,o) = 0.92*a*l + 0.68*a*(1-l) + 0.55*(1-a)*l + 0.12*(1-a)*(1-l)`

`= 0.12 + 0.56*a + 0.43*l - 0.19*a*l`.

For O=High this is `0.4425 + 0.4175*a`; for O=Low it is
`0.2705 + 0.4935*a`. The remaining sum has six terms:''']
    manual = []
    for w, p_w in zip(STATES['W'], (0.5, 0.3, 0.2)):
        for o, p_o in [('High', 0.555), ('Low', 0.445)]:
            a = model['A'][(w, o)][0]
            load = model['L'][(o,)][0]
            g = 0.12 + 0.56 * a + 0.43 * load - 0.19 * a * load
            manual.append((w, o, f'{p_w*p_o:.6f}', f'{g:.8f}', f'{p_w*p_o*g:.10f}'))
    sections += [table(['W', 'O', 'P(w)P(o)', 'g(w,o)', 'Contribution'], manual),
                 '''Adding these contributions gives **0.5806310375**, matching exact code
inference to floating-point precision.

## B. Conditional independence

1. **W is independent of D.** The simple paths W -> A <- O <- D and
   W -> A -> E <- L <- O <- D are blocked by colliders A and E respectively.
2. **W is not independent of D given E.** Conditioning on E opens the collider
   E in the second path. E is also a descendant of collider A, so observing E
   opens the first path.
3. **W is independent of L given O.** The path W -> A <- O -> L is blocked by
   conditioned noncollider O (and its unobserved collider A). The other path
   W -> A -> E <- L is blocked by the unobserved collider E.

Numerical checks:''',
                 table(['Comparison', 'First value', 'Second value'], [
                     ['P(W=Hot) vs P(W=Hot given D=Weekend)', f'{results["independence"]["weather_hot"]:.10f}', f'{results["independence"]["weather_hot_given_weekend"]:.10f}'],
                     ['P(W=Hot given E=High) vs also D=Weekend', f'{results["independence"]["weather_hot_given_high_energy"]:.10f}', f'{results["independence"]["weather_hot_given_high_energy_weekend"]:.10f}'],
                     ['P(W=Hot given O=High) vs also L=Heavy', f'{results["independence"]["weather_hot_given_high_occupancy"]:.10f}', f'{results["independence"]["weather_hot_given_high_occupancy_heavy_load"]:.10f}']]),
                 '''`independence_checks.csv` checks every W,D state pair unconditionally and
for both E values, and every W,L state pair for both O values. Independence
uses joint-versus-product comparisons; one unequal pair is sufficient to
disprove conditional independence.

## C. Synthetic data

The sampler is implemented directly, without a library sampling routine.
It visits W,D,O,A,L,E in topological order and draws each state using the
appropriate CPT cumulative probability. The seed is **2026**, using Python's
`random.Random`. Generate 20,000 rows once and take prefixes of length 500,
5,000, and 20,000. The datasets are nested, not independent replicates.
The three CSV files contain the actual generated data.''']
    for size, data in results['datasets'].items():
        sections += [f'### Dataset size {size}\n\n' + table(['Weather', 'Count', 'Frequency'],
                    [(w, count, f'{data["weather_frequencies"][w]:.6f}') for w, count in data['weather_counts'].items()]) +
                    '\n\n' + table(['Weather', 'Occupancy', 'Count'],
                                 [[row['Weather'], row['Occupancy'], row['count']] for row in data['weather_occupancy']])]
    sections += ['''## D. Parameter learning

The structure is held fixed for both estimators. For node i with r states,
q parent configurations, counts N_ijk, and parent count N_ij:

- MLE: `theta_ijk = N_ijk / N_ij`.
- Bayesian BDeu posterior mean: `theta_ijk = (N_ijk + 10/(r*q)) / (N_ij + 10/q)`.

The equivalent sample size is **10 per node**, spread uniformly over all its
CPT cells. Parameters are learned for every node, including both roots. State
spaces are fixed to the specification. All observed datasets contain every
parent configuration, so the uniform fallback for an unidentified MLE row is
never used. Full learned CPTs are saved in the six `cpts_*.json` files.

### Learned AC CPTs

Both On and Off probabilities are shown beside the expert CPT.''']
    for size in results['datasets']:
        sections += [f'#### N = {size}\n\n' + csv_table(ROOT / 'problem1' / 'outputs' / f'ac_cpt_{size}.csv')]
    sections += ['## E. Comparison of query results\n\nAbsolute differences use the unrounded computed values.']
    for size in results['datasets']:
        sections += [f'### N = {size}\n\n' + csv_table(ROOT / 'problem1' / 'outputs' / f'comparison_{size}.csv')]
    sections += ['### Mean absolute difference\n\n' + table(['Dataset size', 'MLE', 'BDeu'],
                 [[size, f'{data["MLE"]["mean_absolute_error"]:.9f}', f'{data["BDeu"]["mean_absolute_error"]:.9f}']
                  for size, data in results['datasets'].items()]),
                 '![Mean absolute difference versus dataset size](../problem1/outputs/estimator_comparison.png)',
                 '''### Largest error at N=500

Q4 is the largest-error query for both estimators: MLE error **0.037810088**,
BDeu error **0.040152361**. Its evidence W=Cold,O=High has probability
`0.20*0.555=0.111`, or 55.5 expected observations in 500 samples. The actual
dataset has only **45** such rows. This gives relatively little information
about the corresponding AC CPT row. Q4 also uses the learned appliance and
energy CPTs, so its error is not determined by that single evidence count.

### Which estimator performs better?

For this seeded 500-sample dataset, BDeu has the smaller mean absolute
difference: 0.016467440 versus MLE's 0.018827266. Its pseudocounts reduce
variance in sparsely observed CPT rows. This comes with shrinkage toward
uniform probabilities, which can add bias: BDeu is worse on Q2 and Q4 in
this run. It is therefore better on average here, not uniformly better.
Both estimators improve in average error across these three dataset sizes.
Individual queries need not improve monotonically; Q4 worsens between
5,000 and 20,000 rows. One seeded experiment does not establish universal
estimator superiority.''']
    return '\n\n'.join(sections) + '\n'


def problem2_report(metrics):
    sections = ['''# Problem 2: Mars rover sample collection

## 1. Domain modeling

`Domain.pddl` declares only `:strips` and `:typing`. Types are rover, location,
rock, bay, and drill. Predicates record rover, rock and drill locations,
directed connectivity, bay ownership and contents, bay emptiness, rock type,
and permanent drill possession. `move`, `pick-drill`, `collect-soft`,
`collect-hard`, and `deposit` implement the four conceptual actions; collect
is split into two STRIPS actions to avoid disjunctive or negative preconditions.

Collection requires co-location and an empty owned bay, removes the rock's
ground location, and fills that bay. Hard collection additionally requires
the drill. Deposit is allowed at the current location, including locations
other than Base, as the brief permits. Pickup permanently records possession
of the drill; it does not consume a rock storage bay. Negative **effects**
are normal STRIPS deletes; no negative **preconditions** are used.

## 2. Problem modeling

`Problem.pddl` contains Curiosity, two empty bays, Drill1 at SiteE, and the
five rocks at their specified sites. Each two-way connection is represented
by two facts. Only SiteC -> SiteD is added for the downhill route.

`Problem_extended.pddl` adds soft Rock6 at SiteE and hard Rock7 at SiteF.
Both Base -> SiteB and SiteB -> Base are absent. Goals require all rocks
and the rover at Base; both bays must also be empty. Explicit empty-bay
goals in the extended problem are consistent with the base mission and
already follow from all rocks being on the ground at Base.

## 3. Search configurations and measured results

Pyperplan 2.1 parses and grounds the submitted PDDL files. Grounded operators
are sorted by name, and subprocesses fix `PYTHONHASHSEED=0` for repeatable
tie-breaking. Every action has unit cost.

- Satisficing: greedy best-first search with the FF delete-relaxation heuristic.
- Optimal: A* with the admissible rover lower bound implemented in
  `lower_bound.py`. No preferred-operator pruning or weighted A* is used.

### Why the A* heuristic is admissible

The handling bound counts two actions per undelivered ground rock (collect,
deposit), one per carried rock (deposit), and one drill pickup when an
undelivered hard rock requires it. These handling actions are necessary.

For movement, a cached dynamic program computes the shortest directed route
from the current location through every remaining ground-rock site and the
drill site when needed, ending at Base. It ignores storage capacity and
ordering constraints. Any real completion visits these sites, so this is
a movement lower bound. A second bound is the ceiling of half the sum of
the shortest distances to Base of all undelivered rocks, with carried rocks
starting at the rover. Each move transports at most two rocks by one edge.

The heuristic adds the handling bound to the **maximum** of these movement
bounds. Handling and movement use disjoint action types. Hence the total
never exceeds the true remaining action count and is zero at the goal.
Pyperplan's A* reopens states when a cheaper path is found, so consistency
is not needed for the optimality guarantee.

### Results

These are measured run results, not estimated runtimes. Planning wall time
includes parsing, grounding, and heuristic setup but excludes validation and
file writing. Search time excludes setup. Node counts follow Pyperplan's
convention and include the popped goal node. Plan length and total number
of executed actions are identical here because each plan is sequential.''']
    sections += [table(['Scenario', 'Search', 'Plan length / total actions', 'Nodes expanded', 'Search time (s)', 'Planning time (s)'],
                 [[m['scenario'], m['search'], m['plan_length'], m['nodes_expanded_including_goal'],
                   f'{m["search_wall_seconds"]:.6f}', f'{m["planning_wall_seconds"]:.6f}'] for m in metrics]),
                 '''### Complete action sequences

Each sequence below comes directly from the generated `.plan` file.
The corresponding `.json` files contain timings, action counts, and goals.''']
    for m in metrics:
        name = f'{m["scenario"]}_{m["search"]}'
        plan = (ROOT / 'problem2' / 'outputs' / f'{name}.plan').read_text()
        sections += [f'#### {m["scenario"].title()} / {m["search"]}\n\n```text\n' +
                     '\n'.join(f'{i:02}. {line}' for i, line in enumerate(plan.splitlines(), 1)) + '\n```']
    sections += ['''## 4. Goal verification

Every plan was replayed using the full grounded PDDL preconditions and
effects, with static facts and all operators retained. A separate simulator
implements the rover's movement, pickup, collection, and deposit rules.
The two final states must agree exactly. At every step it checks that the
rover has one location, each rock has one location or bay, each bay holds
at most one rock, and empty flags match bay contents. Preconditions also
check route direction, ownership, co-location, rock type, and drill possession.

All four plans passed both replays. The `.trace.txt` files show the dynamic
state after every action. The original plans finish with Rock1-Rock5 at Base;
the extended plans finish with Rock1-Rock7 at Base. Curiosity is at Base and
Bay1 and Bay2 are empty in every final state. The drill remains carried.
VAL was not used; validation was performed by the two described simulators.

## 5. Extended scenario

The storm removes only the Base-SiteB route. SiteB remains reachable through
SiteD. The optimal plan reaches SiteD by Base -> SiteA -> SiteC -> SiteD,
then reaches SiteB from SiteD. On returning, it travels SiteB -> SiteD ->
SiteE -> SiteC -> SiteA -> Base. It never uses the closed route or the
forbidden direct SiteD -> SiteC move.

## 6. Plan analysis

The original greedy plan takes 30 actions while A* takes 25. Both perform
five collections, five deposits, and one drill pickup; the difference is
19 versus 14 moves. The greedy heuristic chooses locally useful deliveries
and creates extra travel. The extended plans take 44 and 40 actions, with
29 and 25 moves respectively; both use seven collections, seven deposits,
and one pickup. The extra rocks and route closure increase required travel.

In the original optimal plan, Rock2 and Rock4 share the first return trip.
The rover then picks up the drill at **step 12**, before collecting Rock5
and Rock3 into the two bays. These are returned together. Rock1 is delivered
on the final short trip. Every hard-rock collection follows drill pickup.

In the extended optimal plan, Rock4 and Rock2 share the first return trip.
The rover picks up the drill at **step 9** while carrying them back, so later
hard-rock collections are enabled. Rock5 and Rock7 share the next trip from
SiteF, followed by Rock6 and Rock3, then Rock1. The directed SiteC -> SiteD
slope is used at **step 3**. Both bays are used whenever a useful pair is
available. These are particular optimal plans; another optimal sequence
may deliver rocks or choose bays in a different order.

## Planner reference

[Pyperplan source and usage](https://github.com/aibasel/pyperplan) documents
the STRIPS planner. This submission uses the installed **2.1** API; its
internal search registry calls greedy search `gbf`, while our wrapper uses
the clearer argument `--search gbfs`.''']
    return '\n\n'.join(sections) + '\n'


def problem3_report():
    runtime = json.loads((ROOT / 'problem3/outputs/runtime.json').read_text())['version']
    return '''# Problem 3: Royal archive access verification

## 1. Knowledge representation

Constants are `mira`, `scroll_7`, and `royal_archive`. Variables x,y denote
people or records as appropriate in this single-sorted FOL encoding.

| Predicate | Meaning |
| --- | --- |
| Archivist(x) | x is an archivist |
| Verifies(x,r) | x verifies record r |
| Trusted(x) | x is trusted |
| Access(x,r) | x has access to r |
| Sealed(r) | r is sealed |
| Permitted(x,r) | x may inspect r |
| Inspects(x,r) | x actually inspects r |
| FindsMark(x,r) | x finds a hidden mark in r |
| Stored(r,a) | r is stored in archive a |

The formulas are:

1. `forall x,r: (Archivist(x) and Verifies(x,r)) -> Trusted(x)`.
2. `forall x,r: (Trusted(x) and Access(x,r) and Sealed(r)) -> Permitted(x,r)`.
3. `forall x,r: (Inspects(x,r) and FindsMark(x,r)) -> Verifies(x,r)`.
4. `forall r: Stored(r,royal_archive) -> Sealed(r)`.
5. `Stored(scroll_7,royal_archive)`.
6. `Access(mira,scroll_7)`.
7. `Inspects(mira,scroll_7) and FindsMark(mira,scroll_7)`.
8. `Archivist(mira)`.

`Permitted` and `Inspects` are different predicates. Permission does not
imply that an inspection actually occurred.

## 2. Negate the goal

The goal is `Trusted(mira)`. Add `not Trusted(mira)` to the knowledge base.
The program does not add the positive goal as a fact.

## 3. Conversion to clause form

The program represents formulas as terms and performs each transformation.
Implications become `not antecedent or consequent`. De Morgan's laws move
negations to predicates. For example, the first rule becomes

`forall x,r: not Archivist(x) or not Verifies(x,r) or Trusted(x)`.

Bound variables are renamed freshly for each scope. Clauses use distinct
variables across rules, and each resolution parent is copied separately
to standardize variables apart again. Variables printed as A,B in different
clauses are local to their clauses, not shared across them.

There are no existential quantifiers, so Skolemization introduces no new
symbols. Universal quantifiers are omitted in clause form. Disjunction is
distributed over conjunction when needed; the conjunction of the two
ground facts in formula 7 produces two unit clauses.

All variables in the following clauses are universally quantified:

| Clause | Literals |
| --- | --- |
| C1 | not Archivist(x1) or not Verifies(x1,r1) or Trusted(x1) |
| C2 | not Trusted(x2) or not Access(x2,r2) or not Sealed(r2) or Permitted(x2,r2) |
| C3 | not Inspects(x3,r3) or not FindsMark(x3,r3) or Verifies(x3,r3) |
| C4 | not Stored(r4,royal_archive) or Sealed(r4) |
| C5 | Stored(scroll_7,royal_archive) |
| C6 | Access(mira,scroll_7) |
| C7 | Inspects(mira,scroll_7) |
| C8 | FindsMark(mira,scroll_7) |
| C9 | Archivist(mira) |
| C10 | not Trusted(mira) |

## 4. Prolog implementation

`royal_archive_access.pl` contains the required eight labeled sections.
`main/0` prints the formulas, transformation stages, clauses, and proof.
`resolve/5` selects complementary literals, performs unification with an
occurs check, and returns the remaining literals. Set-of-support resolution
starts from the negated goal and prefers shorter new resolvents. This is a
procedure for the supplied knowledge base, not a claim of a complete
general-purpose first-order theorem prover.

## 5. Resolution refutation

The executed proof produces the following resolvents in order. Clause
variables are renamed below for readability; literal order is immaterial.

| New clause | Parents | Unification | Resolvent |
| --- | --- | --- | --- |
| C11 | C1, C10 | x1=mira | not Archivist(mira) or not Verifies(mira,r1) |
| C12 | C9, C11 | ground Archivist literal | not Verifies(mira,r1) |
| C13 | C3, C12 | x3=mira, r3=r1 | not Inspects(mira,r1) or not FindsMark(mira,r1) |
| C14 | C7, C13 | r1=scroll_7 | not FindsMark(mira,scroll_7) |
| C15 | C8, C14 | identical ground mark literals | [] |

C15 is the empty clause, a contradiction. Therefore the original knowledge
base entails `Trusted(mira)`. The substantive chain is that the observed
inspection and mark establish verification, and verification plus archivist
status establish trust. Rules about sealing, access and permission are not
needed for this conclusion.

## 6. Proof verification

The saved `outputs/proof_output.txt` is actual SWI-Prolog output. It ends
with `C15 = []`, the verified conclusion, and a passing self-test message.
The program replays every recorded resolution step against its parents.
Self-tests check preservation of repeated variables in CNF, ordinary and
occurs-check unification, absence of an assumed positive goal, and failure
to refute after separately removing the inspection, mark, or archivist fact.

Run manually from the repository root:

```powershell
swipl -q -s problem3/royal_archive_access.pl -g main -t halt
```

Use `screenshots/README.md` to capture genuine execution screenshots.

## Runtime reference

[SWI-Prolog downloads](https://www.swi-prolog.org/download/stable) provides
the runtime. The verified run used SWI-Prolog 10.0.2 for x64 Windows.
'''.replace('SWI-Prolog 10.0.2 for x64 Windows', runtime)


def html_page(title, body):
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1120px;margin:36px auto;padding:0 24px;color:#182333}}
h1,h2,h3,h4{{line-height:1.25}}h1{{border-bottom:2px solid #284c66;padding-bottom:12px}}h2{{margin-top:36px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:20px 0}}td,th{{border:1px solid #b9c6d2;padding:8px;text-align:left}}
th{{background:#edf3f7}}pre{{background:#f1f4f7;padding:18px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 Consolas,monospace}}
code{{font-size:.9em}}img{{max-width:100%}}a{{color:#175d91}}.source{{background:#eef4f7;padding:12px}}
@media print{{body{{margin:0;font-size:10pt;max-width:none}}h2{{break-after:avoid}}tr,img{{break-inside:avoid}}pre{{font-size:8pt}}}}
</style><body>{body}</body></html>'''


def capture_views(metrics):
    folder = REPORTS / 'capture_views'
    folder.mkdir(exist_ok=True)
    output = (ROOT / 'problem1/outputs/run_output.txt').read_text()
    views = {}
    views['problem1_queries'] = ('Problem 1: expert queries', 'problem1/outputs/run_output.txt',
                                 'python problem1/run_analysis.py', '<pre>' + escape(output.split('\nN = ')[0]) + '</pre>')
    for size in (500, 5000, 20000):
        section = output.split(f'\nN = {size}\n')[1].split('\nN = ')[0]
        views[f'problem1_{size}'] = (f'Problem 1: N={size}', 'problem1/outputs/run_output.txt',
                                    'python problem1/run_analysis.py', '<pre>' + escape(section) + '</pre>')
    for name, filename in [('network', 'network.png'), ('comparison', 'estimator_comparison.png')]:
        views[f'problem1_{name}'] = (f'Problem 1: {name}', f'problem1/outputs/{filename}',
                                    'python problem1/run_analysis.py', f'<img style="max-height:68vh" src="../../problem1/outputs/{filename}">')
    for m in metrics:
        name = f'{m["scenario"]}_{m["search"]}'
        plan = (ROOT / 'problem2/outputs' / f'{name}.plan').read_text()
        numbered = '\n'.join(f'{i:02}. {line}' for i, line in enumerate(plan.splitlines(), 1))
        summary = (f'Plan length / total actions: {m["plan_length"]}; expanded nodes (including goal): {m["nodes_expanded_including_goal"]}; '
                   f'search: {m["search_wall_seconds"]:.6f} s; planning: {m["planning_wall_seconds"]:.6f} s')
        body = '<p>' + escape(summary) + '</p><pre style="column-count:2;column-gap:24px;white-space:pre;font-size:12px">' + escape(numbered) + '</pre>'
        body += '<p><strong>FINAL GOALS VERIFIED</strong>: all rocks at Base; Curiosity at Base; Bay1 and Bay2 empty.</p>'
        views[f'problem2_{name}'] = (f'Problem 2: {name}', f'problem2/outputs/{name}.log and .plan',
                                   f'python problem2/run_planner.py --scenario {m["scenario"]} --search {m["search"]}', body)
    proof = (ROOT / 'problem3/outputs/proof_output.txt').read_text(encoding='utf-8-sig')
    views['problem3_proof'] = ('Problem 3: final resolution proof', 'problem3/outputs/proof_output.txt',
                              'swipl -q -s problem3/royal_archive_access.pl -g main -t halt',
                              '<pre>' + escape(proof[proof.index('RESOLUTION TRACE'):]) + '</pre>')
    for name, (title, source, command, body) in views.items():
        banner = f'<h1>{escape(title)}</h1><p class="source"><strong>Saved-output view</strong> from a verified run; not a live terminal.<br>Source: {escape(source)}<br>Re-run: <code>{escape(command)}</code></p>'
        (folder / f'{name}.html').write_text(html_page(title, banner + body), encoding='utf-8')


def main():
    REPORTS.mkdir(exist_ok=True)
    results = json.loads((ROOT / 'problem1/outputs/results.json').read_text())
    metrics = [json.loads((ROOT / 'problem2/outputs' / f'{scenario}_{search}.json').read_text())
               for scenario in ('original', 'extended') for search in ('gbfs', 'astar')]
    contents = {'problem1_analysis.md': problem1_report(results),
                'problem2_analysis.md': problem2_report(metrics),
                'problem3_analysis.md': problem3_report()}
    for name, content in contents.items():
        (REPORTS / name).write_text(content, encoding='utf-8')
    members = (ROOT / 'GROUP_MEMBERS.md').read_text()
    combined = '# AI Group Assignment 2\n\n' + members.replace('# Group members', '## Group members', 1)
    combined += '\n\n' + '\n\n'.join(contents.values())
    combined += '\n\n# AI reporting check\n\n' + (REPORTS / 'AI_INSTRUCTIONS.md').read_text().split('\n', 1)[1]
    (REPORTS / 'REPORT.md').write_text(combined, encoding='utf-8')
    from markdown_it import MarkdownIt
    renderer = MarkdownIt().enable('table')
    (REPORTS / 'REPORT.html').write_text(html_page('Old I.N.D - Assignment 2', renderer.render(combined)), encoding='utf-8')
    body = '<h1>Verified saved program outputs</h1><p>These views display actual saved run outputs. They are not live terminal sessions. Re-run commands are provided below and in the repository README.</p>'
    body += '<nav><a href="#bayesian">Bayesian</a> | <a href="#planning">Planning</a> | <a href="#proof">Prolog proof</a></nav>'
    body += '<section id="bayesian"><h2>Problem 1: Bayesian analysis</h2><p class="source">Source: problem1/outputs/run_output.txt<br>Run: python problem1/run_analysis.py</p><pre>'
    body += escape((ROOT / 'problem1/outputs/run_output.txt').read_text()) + '</pre>'
    body += '<h3>Generated network figure</h3><img src="../problem1/outputs/network.png" alt="Bayesian network">'
    body += '<h3>Generated estimator comparison</h3><img src="../problem1/outputs/estimator_comparison.png" alt="Estimator errors"></section>'
    body += '<section id="planning"><h2>Problem 2: verified planner output</h2>'
    for m in metrics:
        name = f'{m["scenario"]}_{m["search"]}'
        body += f'<h3 id="{name}">{escape(name)}</h3><p class="source">Source: problem2/outputs/{name}.log<br>Run: python problem2/run_planner.py --scenario {m["scenario"]} --search {m["search"]}</p>'
        body += '<pre>' + escape((ROOT / 'problem2/outputs' / f'{name}.log').read_text()) + '</pre>'
    body += '</section><section id="proof"><h2>Problem 3: executed resolution proof</h2>'
    body += '<p class="source">Source: problem3/outputs/proof_output.txt (SWI-Prolog 10.0.2)<br>Run: swipl -q -s problem3/royal_archive_access.pl -g main -t halt</p>'
    proof = (ROOT / 'problem3/outputs/proof_output.txt').read_text(encoding='utf-8-sig')
    body += '<pre>' + escape(proof[proof.index('RESOLUTION TRACE'):]) + '</pre></section>'
    (REPORTS / 'evidence.html').write_text(html_page('Verified program evidence', body), encoding='utf-8')
    runtime = json.loads((ROOT / 'problem3/outputs/runtime.json').read_text())
    environment = {'python': platform.python_version(), 'platform': platform.platform(),
                   'numpy': results['numpy'], 'matplotlib': results['matplotlib'],
                   'pyperplan': metrics[0]['planner_version'], 'swipl': runtime['version'],
                   'seed': results['seed'], 'hash_seed': 0}
    (REPORTS / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n', encoding='utf-8')
    capture_views(metrics)
    print('Built three analysis reports, combined Markdown/HTML report, and saved-output viewer.')


if __name__ == '__main__':
    main()
