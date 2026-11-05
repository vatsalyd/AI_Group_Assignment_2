# AI Group Assignment 2

Group: **Old I.N.D**. Names, roll numbers, and responsibilities are in
[GROUP_MEMBERS.md](GROUP_MEMBERS.md).

## Read the results

Open [reports/REPORT.html](reports/REPORT.html) in a browser for the complete
report, or read [reports/REPORT.md](reports/REPORT.md). Separate reports are
available for each problem. The report includes all inference tables, the
hand calculation, independence arguments, planning sequences and analysis,
and the FOL resolution proof.

| Folder | Contents |
| --- | --- |
| `problem1/` | Bayesian code, three generated datasets, CPTs, tables, figures |
| `problem2/` | Three required PDDL files, planner wrapper, heuristic, four plans and state traces |
| `problem3/` | Required single Prolog file and actual proof output |
| `reports/` | Analysis, environment, verification log |
| `tests/` | Inference and planning checks |
| `screenshots/` | Capture instructions and genuine captures, when present |
| `scripts/` | Reproduction, report generation, and packaging |

## Install dependencies

Use Python 3.14 (verified with 3.14.8) and SWI-Prolog (verified with 10.0.2).
From PowerShell in the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install SWI-Prolog from its [official download page](https://www.swi-prolog.org/download/stable)
and put `swipl` on PATH, or supply its executable path to `--swipl`.
The local `tools/swipl/bin/swipl.exe` is used automatically when present;
downloaded runtimes and planner packages are excluded from Git and the ZIP.

## Reproduce everything

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py
```

If Prolog is not on PATH:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --swipl 'C:\Program Files\swipl\bin\swipl.exe'
```

The runner stops on a failed command or unexpected proof warning. It regenerates
the datasets, figures, four plans, proof log, tests, and reports. It does not
capture or synthesize screenshots. Runtimes can change between runs. Plan
tie-breaking is fixed; Bayesian sampling uses seed 2026 and nested datasets.

## Run each part manually

```powershell
python problem1/run_analysis.py
python problem2/run_planner.py --scenario original --search gbfs
python problem2/run_planner.py --scenario original --search astar
python problem2/run_planner.py --scenario extended --search gbfs
python problem2/run_planner.py --scenario extended --search astar
swipl -q -s problem3/royal_archive_access.pl -g main -t halt
python -m unittest discover -s tests -v
python scripts/build_reports.py
```

Use `.\.venv\Scripts\python.exe` in place of `python` when dependencies are
installed in the virtual environment. On this machine the portable Prolog
equivalent is:

```powershell
& '.\tools\swipl\bin\swipl.exe' -q -s problem3/royal_archive_access.pl -g main -t halt
```

## Screenshots and submission

Follow [screenshots/README.md](screenshots/README.md). Figures are program-generated
plots, not execution screenshots. `reports/evidence.html` transparently displays
saved, verified output and can be opened for inspection. Browser captures of
this viewer, if included, are labeled as saved-output views.

Create the ZIP after verification and screenshot capture:

```powershell
python scripts/package_submission.py
```

The packaging script checks required files and creates a SHA-256 manifest.
Use `--require-screenshots` to require the listed captures before packaging.
The ZIP excludes `.git`, virtual environments, local tools, and caches.
