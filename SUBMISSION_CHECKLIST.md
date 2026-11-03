# Submission checklist

Group: **Old I.N.D**

## Completed and executed

- [x] Names, roll numbers, and question allocation recorded as supplied.
- [x] Expert Bayesian network, normalized CPTs, graph, Q1-Q7, explaining away,
  hand calculation, and numerical independence checks.
- [x] Seeded ancestral sampling for 500, 5,000, and 20,000 rows; actual CSVs,
  weather frequencies, and weather/occupancy counts.
- [x] MLE and BDeu (ESS=10) for all dataset sizes; full learned CPTs, AC CPT
  comparisons, all query comparisons, error plot, and written interpretation.
- [x] Three required PDDL files using only STRIPS and typing.
- [x] Four generated plans: two scenarios, two searches; measured times,
  expansion counts, action sequences, lengths, and action totals.
- [x] All four plans replayed by two simulators; intermediate and final states saved.
- [x] Eight Prolog sections, actual FOL-to-CNF transformations, ordered resolution
  trace, derived empty clause, and proof checks executed in SWI-Prolog.
- [x] Complete analysis report and reproducible run commands.
- [x] AI instruction check documented; no explicit AI disclosure requirement found
  in the supplied PDF. Separate course policy remains unknown.
- [x] Local Git repository with focused commits.

## Manual work still required

- [ ] Capture genuine execution and visualization screenshots using
  `screenshots/README.md` or `scripts/capture_manual.ps1`.
- [ ] Review the work with the assigned group members.
- [ ] After adding screenshots, run `python scripts/package_submission.py --require-screenshots`.

Screenshot capture through Computer Use ended because the tool could not verify
the local browser URL sufficiently to enforce its policy. No screenshot images
were manufactured. The current ZIP includes the verified code, outputs, report,
and capture instructions, but is **not ready to submit until screenshots are added**.
