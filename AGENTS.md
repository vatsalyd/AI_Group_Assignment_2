# Repository Guidelines

## Project Structure & Module Organization

The repository currently contains only `AI_group_assignment_02_2026.pdf`, the assignment specification. No source directories, dependency manifests, test suites, or build configuration exist yet. Preserve the PDF as the reference for requirements.

Organize new work by assignment problem:

- `problem1/`: Python Bayesian network implementation, sampling, inference, and estimator comparisons.
- `problem2/`: `Domain.pddl`, `Problem.pddl`, `Problem_extended.pddl`, and planner outputs.
- `problem3/`: `royal_archive_access.pl`, including transformation stages and resolution traces.
- `reports/` and `screenshots/`: analysis, visualizations, and proof evidence.

These directories are proposed conventions; create them as implementations are added.

## Build, Test, and Development Commands

There is no configured build or test command. Document exact dependencies, versions, entry points, and planner search configurations alongside each solution.

Once the proposed files exist, useful checks include:

- `python -m compileall problem1`: check Python syntax; this does not validate inference results.
- `swipl -s problem3/royal_archive_access.pl`: load the Prolog program in SWI-Prolog, if selected. Document the predicate that executes the proof.

Record reproducible planner commands for both satisficing and optimal searches; do not assume a planner is installed.

## Coding Style & Naming Conventions

Use four-space indentation and `snake_case` functions and variables in Python. Keep Bayesian variable names, state ordering, and CPT parent ordering consistent. Use lowercase Prolog predicates and atoms, uppercase variables, and the assignment's eight labeled transformation stages. Preserve the specified PDDL filenames and use consistent predicate names. No formatter or linter is configured.

## Testing Guidelines

No testing framework or coverage threshold is established. Verify CPT normalization, Q1 against the handwritten calculation, conditional independence claims, and reproducible sampling with a reported seed. Validate both rover scenarios by replaying plans and checking final goals, bay capacity, drill requirements, and route direction. Confirm the Prolog trace derives the empty clause `[]`. Keep validation commands and expected results with each solution.

## Commit & Pull Request Guidelines

No Git history is available to establish commit conventions. Use concise, imperative messages such as `Add ancestral sampling validation`. Keep changes focused on one problem or shared documentation. Pull requests should describe the affected tasks, execution commands, validation results, and relevant output screenshots.

## Submission Checklist

Prepare one ZIP containing source code, required reports, planner outputs, and screenshots. Include every group member's name and roll number, as required by the assignment brief.
