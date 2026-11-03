# Genuine screenshot capture

Do not generate terminal-looking images or rename plots as screenshots.
Run the commands below in a visible terminal, check success, then use the
Windows Snipping Tool manually. Include the command, readable output, and
application window. Save PNG files under the names listed here.

## 1. Bayesian output

From the repository root:

```powershell
python problem1/run_analysis.py
```

Capture the expert queries as `problem1_queries.png` and each dataset's
AC CPT, query comparison, and counts as `problem1_500.png`,
`problem1_5000.png`, and `problem1_20000.png`. Use multiple captures if a
single window cannot show the results readably. The complete text is saved
in `problem1/outputs/run_output.txt`.

Open `problem1/outputs/network.png` and
`problem1/outputs/estimator_comparison.png` in an image viewer and capture
them as `problem1_network.png` and `problem1_comparison.png`.
The original PNGs are generated figures; these captures show them in an app.

## 2. Planner output

```powershell
python problem2/run_planner.py --scenario original --search gbfs
python problem2/run_planner.py --scenario original --search astar
python problem2/run_planner.py --scenario extended --search gbfs
python problem2/run_planner.py --scenario extended --search astar
```

Save `problem2_original_gbfs.png`, `problem2_original_astar.png`,
`problem2_extended_gbfs.png`, and `problem2_extended_astar.png`. Include
plan length, expanded nodes, timing, and `FINAL GOALS VERIFIED`. Full plans
and intermediate states are already saved in the output folder.

## 3. Final Prolog proof

```powershell
swipl -q -s problem3/royal_archive_access.pl -g main -t halt
```

Or use the local runtime on this machine:

```powershell
& '.\tools\swipl\bin\swipl.exe' -q -s problem3/royal_archive_access.pl -g main -t halt
```

Save `problem3_proof.png` showing the resolution trace, `C15 = []`,
the verified conclusion, and `SELF-TEST PASS`.

## Saved-output browser views

`reports/evidence.html` displays the actual saved outputs with source filenames
and rerun commands. Any supplied browser screenshots of that page are genuine
captures of saved-output views, not screenshots of a live terminal execution.
See `CAPTURE_MANIFEST.md` when present for the exact capture provenance.

Reproduce a browser view by opening the local file and navigating to the
Bayesian, planning, or Prolog section. Take a normal screenshot of the browser.
Manual terminal screenshots above can replace the browser views if the
instructor expects the execution console specifically.
