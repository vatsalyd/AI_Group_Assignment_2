import argparse
import json
import os
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
    output = ROOT / 'problem3' / 'outputs'
    output.mkdir(exist_ok=True)
    version = execute([swipl, '--version'], capture_output=True, text=True, encoding='utf-8')
    (output / 'runtime.json').write_text(json.dumps({'version': version.stdout.strip(),
                                                 'executable': swipl}, indent=2) + '\n', encoding='utf-8')
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
    (output / 'proof_output.txt').write_text(result.stdout, encoding='utf-8')
    print(result.stdout)
    execute([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    execute([sys.executable, 'scripts/build_reports.py'])
    print('ALL RUNS AND CHECKS PASSED')


if __name__ == '__main__':
    if '--worker' in sys.argv:
        sys.argv.remove('--worker')
        main()
    else:
        log = ROOT / 'reports' / 'verification_run.txt'
        log.parent.mkdir(exist_ok=True)
        environment = dict(os.environ, PYTHONIOENCODING='utf-8')
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run([sys.executable, __file__, '--worker', *sys.argv[1:]],
                                    cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        print(log.read_text(encoding='utf-8'))
        raise SystemExit(result.returncode)
