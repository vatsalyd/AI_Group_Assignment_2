import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ('problem1_queries.png', 'problem1_500.png', 'problem1_5000.png',
            'problem1_20000.png', 'problem1_network.png', 'problem1_comparison.png',
            'problem2_original_gbfs.png', 'problem2_original_astar.png',
            'problem2_extended_gbfs.png', 'problem2_extended_astar.png', 'problem3_proof.png')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-screenshots', action='store_true')
    args = parser.parse_args()
    required = ['GROUP_MEMBERS.md', 'reports/REPORT.md', 'reports/REPORT.html',
                'reports/verification_run.txt', 'problem1/bayesian_network.py',
                'problem1/run_analysis.py', 'problem1/outputs/results.json',
                'problem1/outputs/network.png', 'problem1/outputs/estimator_comparison.png',
                'problem2/Domain.pddl', 'problem2/Problem.pddl', 'problem2/Problem_extended.pddl',
                'problem3/royal_archive_access.pl', 'problem3/outputs/proof_output.txt']
    for size in (500, 5000, 20000):
        required += [f'problem1/outputs/{name}_{size}.csv' for name in ('data', 'comparison', 'ac_cpt')]
    for scenario in ('original', 'extended'):
        for search in ('gbfs', 'astar'):
            required += [f'problem2/outputs/{scenario}_{search}{suffix}' for suffix in ('.plan', '.log', '.json', '.trace.txt')]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Missing deliverables: ' + ', '.join(missing))
    missing_captures = [name for name in CAPTURES if not (ROOT / 'screenshots' / name).is_file()]
    if args.require_screenshots and missing_captures:
        raise SystemExit('Missing screenshots: ' + ', '.join(missing_captures))
    verification = (ROOT / 'reports/verification_run.txt').read_text(encoding='utf-8-sig')
    if 'ALL RUNS AND CHECKS PASSED' not in verification:
        raise SystemExit('Full verification has not completed successfully')
    output = ROOT / 'submission'
    output.mkdir(exist_ok=True)
    files = [ROOT / filename for filename in ('README.md', 'AGENTS.md', 'GROUP_MEMBERS.md', 'SUBMISSION_CHECKLIST.md',
              'requirements.txt', 'AI_group_assignment_02_2026.pdf', '.gitignore')]
    for folder in ('problem1', 'problem2', 'problem3', 'reports', 'tests', 'scripts', 'screenshots'):
        files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    files = sorted(set(files))
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (output / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    status = {'included_files': len(files), 'missing_screenshots': missing_captures,
              'verification': 'ALL RUNS AND CHECKS PASSED',
              'screenshot_provenance': 'See screenshots/CAPTURE_MANIFEST.md if captures are included'}
    (output / 'STATUS.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    destination = output / 'Old_IND_AI_Assignment_2.zip'
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(output / 'SHA256SUMS.json', 'SHA256SUMS.json')
        archive.write(output / 'STATUS.json', 'SUBMISSION_STATUS.json')
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for name, digest in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest, name
    print(f'Created and verified: {destination}')
    print(f'Included files: {len(files)}; missing screenshots: {len(missing_captures)}')


if __name__ == '__main__':
    main()
