# Problem 2: Mars rover sample collection

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
of executed actions are identical here because each plan is sequential.

| Scenario | Search | Plan length / total actions | Nodes expanded | Search time (s) | Planning time (s) |
| --- | --- | --- | --- | --- | --- |
| original | gbfs | 30 | 45 | 0.020313 | 0.034690 |
| original | astar | 25 | 1327 | 0.049267 | 0.063923 |
| extended | gbfs | 44 | 91 | 0.059906 | 0.073669 |
| extended | astar | 40 | 153190 | 7.030539 | 7.046653 |

### Complete action sequences

Each sequence below comes directly from the generated `.plan` file.
The corresponding `.json` files contain timings, action counts, and goals.

#### Original / gbfs

```text
01. (move curiosity base sitea)
02. (collect-soft curiosity rock1 bay1 sitea)
03. (move curiosity sitea base)
04. (deposit curiosity rock1 bay1 base)
05. (move curiosity base siteb)
06. (collect-soft curiosity rock2 bay1 siteb)
07. (move curiosity siteb base)
08. (deposit curiosity rock2 bay1 base)
09. (move curiosity base sitea)
10. (move curiosity sitea sitec)
11. (move curiosity sitec sitee)
12. (pick-drill curiosity drill1 sitee)
13. (move curiosity sitee sitec)
14. (collect-hard curiosity rock3 bay1 sitec)
15. (move curiosity sitec sited)
16. (collect-soft curiosity rock4 bay2 sited)
17. (move curiosity sited siteb)
18. (move curiosity siteb base)
19. (deposit curiosity rock3 bay1 base)
20. (deposit curiosity rock4 bay2 base)
21. (move curiosity base sitea)
22. (move curiosity sitea sitec)
23. (move curiosity sitec sitee)
24. (move curiosity sitee sitef)
25. (collect-hard curiosity rock5 bay1 sitef)
26. (move curiosity sitef sitee)
27. (move curiosity sitee sitec)
28. (move curiosity sitec sitea)
29. (move curiosity sitea base)
30. (deposit curiosity rock5 bay1 base)
```

#### Original / astar

```text
01. (move curiosity base siteb)
02. (collect-soft curiosity rock2 bay1 siteb)
03. (move curiosity siteb sited)
04. (collect-soft curiosity rock4 bay2 sited)
05. (move curiosity sited siteb)
06. (move curiosity siteb base)
07. (deposit curiosity rock2 bay1 base)
08. (deposit curiosity rock4 bay2 base)
09. (move curiosity base sitea)
10. (move curiosity sitea sitec)
11. (move curiosity sitec sitee)
12. (pick-drill curiosity drill1 sitee)
13. (move curiosity sitee sitef)
14. (collect-hard curiosity rock5 bay1 sitef)
15. (move curiosity sitef sitee)
16. (move curiosity sitee sitec)
17. (collect-hard curiosity rock3 bay2 sitec)
18. (move curiosity sitec sitea)
19. (move curiosity sitea base)
20. (deposit curiosity rock3 bay2 base)
21. (deposit curiosity rock5 bay1 base)
22. (move curiosity base sitea)
23. (collect-soft curiosity rock1 bay1 sitea)
24. (move curiosity sitea base)
25. (deposit curiosity rock1 bay1 base)
```

#### Extended / gbfs

```text
01. (move curiosity base sitea)
02. (collect-soft curiosity rock1 bay1 sitea)
03. (move curiosity sitea base)
04. (deposit curiosity rock1 bay1 base)
05. (move curiosity base sitea)
06. (move curiosity sitea sitec)
07. (move curiosity sitec sitee)
08. (pick-drill curiosity drill1 sitee)
09. (collect-soft curiosity rock6 bay1 sitee)
10. (move curiosity sitee sitec)
11. (move curiosity sitec sitea)
12. (move curiosity sitea base)
13. (deposit curiosity rock6 bay1 base)
14. (move curiosity base sitea)
15. (move curiosity sitea sitec)
16. (collect-hard curiosity rock3 bay1 sitec)
17. (move curiosity sitec sitea)
18. (move curiosity sitea base)
19. (deposit curiosity rock3 bay1 base)
20. (move curiosity base sitea)
21. (move curiosity sitea sitec)
22. (move curiosity sitec sited)
23. (move curiosity sited siteb)
24. (collect-soft curiosity rock2 bay1 siteb)
25. (move curiosity siteb sited)
26. (collect-soft curiosity rock4 bay2 sited)
27. (move curiosity sited sitee)
28. (move curiosity sitee sitec)
29. (move curiosity sitec sitea)
30. (move curiosity sitea base)
31. (deposit curiosity rock2 bay1 base)
32. (deposit curiosity rock4 bay2 base)
33. (move curiosity base sitea)
34. (move curiosity sitea sitec)
35. (move curiosity sitec sitee)
36. (move curiosity sitee sitef)
37. (collect-hard curiosity rock5 bay1 sitef)
38. (collect-hard curiosity rock7 bay2 sitef)
39. (move curiosity sitef sitee)
40. (move curiosity sitee sitec)
41. (move curiosity sitec sitea)
42. (move curiosity sitea base)
43. (deposit curiosity rock5 bay1 base)
44. (deposit curiosity rock7 bay2 base)
```

#### Extended / astar

```text
01. (move curiosity base sitea)
02. (move curiosity sitea sitec)
03. (move curiosity sitec sited)
04. (collect-soft curiosity rock4 bay1 sited)
05. (move curiosity sited siteb)
06. (collect-soft curiosity rock2 bay2 siteb)
07. (move curiosity siteb sited)
08. (move curiosity sited sitee)
09. (pick-drill curiosity drill1 sitee)
10. (move curiosity sitee sitec)
11. (move curiosity sitec sitea)
12. (move curiosity sitea base)
13. (deposit curiosity rock2 bay2 base)
14. (deposit curiosity rock4 bay1 base)
15. (move curiosity base sitea)
16. (move curiosity sitea sitec)
17. (move curiosity sitec sitee)
18. (move curiosity sitee sitef)
19. (collect-hard curiosity rock5 bay1 sitef)
20. (collect-hard curiosity rock7 bay2 sitef)
21. (move curiosity sitef sitee)
22. (move curiosity sitee sitec)
23. (move curiosity sitec sitea)
24. (move curiosity sitea base)
25. (deposit curiosity rock5 bay1 base)
26. (deposit curiosity rock7 bay2 base)
27. (move curiosity base sitea)
28. (move curiosity sitea sitec)
29. (move curiosity sitec sitee)
30. (collect-soft curiosity rock6 bay1 sitee)
31. (move curiosity sitee sitec)
32. (collect-hard curiosity rock3 bay2 sitec)
33. (move curiosity sitec sitea)
34. (move curiosity sitea base)
35. (deposit curiosity rock3 bay2 base)
36. (deposit curiosity rock6 bay1 base)
37. (move curiosity base sitea)
38. (collect-soft curiosity rock1 bay1 sitea)
39. (move curiosity sitea base)
40. (deposit curiosity rock1 bay1 base)
```

## 4. Goal verification

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
the clearer argument `--search gbfs`.
