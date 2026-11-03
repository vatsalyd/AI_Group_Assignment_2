import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def execute(command, **kwargs):
    print('\nRUN:', ' '.join(map(str, command)), flush=True)
    if not kwargs.get('capture_output'):
        kwargs.setdefault('stderr', subprocess.STDOUT)
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--swipl', help='Path to swipl executable')
    args = parser.parse_args()
    swipl = args.swipl or shutil.which('swipl')
    local = ROOT / 'tools' / 'swipl' / 'bin' / 'swipl.exe'
    if not swipl and local.exists():
        swipl = str(local)
    if not swipl:
        raise SystemExit('SWI-Prolog is required. Install it or use --swipl PATH.')
    execute([sys.executable, 'problem1/run_analysis.py'])
    for scenario in ('original', 'extended'):
        for search in ('gbfs', 'astar'):
            execute([sys.executable, 'problem2/run_planner.py', '--scenario', scenario, '--search', search])
    command = [swipl, '-q', '-s', 'problem3/royal_archive_access.pl', '-g', 'main', '-t', 'halt']
    result = execute(command, capture_output=True, text=True, encoding='utf-8')
    if result.stderr.strip():
        raise RuntimeError(result.stderr)
    if 'C15 = []' not in result.stdout or 'SELF-TEST PASS' not in result.stdout:
        raise RuntimeError('Proof verification markers are missing')
    output = ROOT / 'problem3' / 'outputs'
    output.mkdir(exist_ok=True)
    (output / 'proof_output.txt').write_text(result.stdout, encoding='utf-8')
    print(result.stdout)
    execute([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    execute([sys.executable, 'scripts/build_reports.py'])
    print('ALL RUNS AND CHECKS PASSED')


if __name__ == '__main__':
    main()
