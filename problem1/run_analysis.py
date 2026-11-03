import csv
import json
from pathlib import Path
import platform
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from bayesian_network import (
    NODES, STATES, PARENTS, QUERIES, ancestral_sample, expert_model,
    joint_distribution, learn_parameters, probability, query_results,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'problem1' / 'outputs'
SEED = 2026
SIZES = (500, 5000, 20000)


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def model_records(model):
    return [{'node': n, 'parents': dict(zip(PARENTS[n], key)),
             'probabilities': dict(zip(STATES[n], values))}
            for n in NODES for key, values in model[n].items()]


def network_plot():
    positions = {'W': (0, 2), 'D': (3, 3), 'O': (3, 2),
                 'A': (1, 1), 'L': (3, 1), 'E': (2, 0)}
    labels = {'W': 'Weather (W)', 'D': 'Day type (D)', 'O': 'Occupancy (O)',
              'A': 'AC usage (A)', 'L': 'Appliance load (L)',
              'E': 'Energy consumption (E)'}
    fig, ax = plt.subplots(figsize=(9, 7))
    for node in NODES:
        for parent in PARENTS[node]:
            ax.annotate('', xy=positions[node], xytext=positions[parent],
                        arrowprops={'arrowstyle': '-|>', 'lw': 1.8,
                                    'shrinkA': 28, 'shrinkB': 30,
                                    'mutation_scale': 20})
    for node, (x, y) in positions.items():
        ax.text(x, y, labels[node], ha='center', va='center',
                bbox={'boxstyle': 'round,pad=0.7', 'fc': '#e4eff7', 'ec': '#295876'})
    ax.set(xlim=(-1, 4), ylim=(-0.6, 3.6), title='Expert Bayesian network')
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(OUT / 'network.png', dpi=180)
    plt.close(fig)


def independence_checks(joint):
    results = []
    for evidence in ({}, {'E': 'High'}, {'E': 'Low'}):
        for w in STATES['W']:
            for d in STATES['D']:
                lhs = probability(joint, {'W': w, 'D': d}, evidence)
                rhs = probability(joint, {'W': w}, evidence) * probability(joint, {'D': d}, evidence)
                results.append({'statement': 'W independent D', 'evidence': str(evidence),
                                'states': f'{w}, {d}', 'joint': lhs,
                                'product': rhs, 'absolute_difference': abs(lhs - rhs)})
    for o in STATES['O']:
        for w in STATES['W']:
            for load in STATES['L']:
                evidence = {'O': o}
                lhs = probability(joint, {'W': w, 'L': load}, evidence)
                rhs = probability(joint, {'W': w}, evidence) * probability(joint, {'L': load}, evidence)
                results.append({'statement': 'W independent L given O', 'evidence': str(evidence),
                                'states': f'{w}, {load}', 'joint': lhs,
                                'product': rhs, 'absolute_difference': abs(lhs - rhs)})
    write_csv(OUT / 'independence_checks.csv', list(results[0]), results)
    return {
        'weather_hot': probability(joint, {'W': 'Hot'}),
        'weather_hot_given_weekend': probability(joint, {'W': 'Hot'}, {'D': 'Weekend'}),
        'weather_hot_given_high_energy': probability(joint, {'W': 'Hot'}, {'E': 'High'}),
        'weather_hot_given_high_energy_weekend': probability(joint, {'W': 'Hot'}, {'E': 'High', 'D': 'Weekend'}),
        'weather_hot_given_high_occupancy': probability(joint, {'W': 'Hot'}, {'O': 'High'}),
        'weather_hot_given_high_occupancy_heavy_load': probability(joint, {'W': 'Hot'}, {'O': 'High', 'L': 'Heavy'}),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expert = expert_model()
    truth = query_results(expert)
    samples = ancestral_sample(expert, max(SIZES), SEED)
    results = {'seed': SEED, 'sampling': 'Nested prefixes of one 20000-row stream',
               'python': platform.python_version(), 'numpy': np.__version__,
               'matplotlib': matplotlib.__version__, 'expert': truth,
               'independence': independence_checks(joint_distribution(expert)), 'datasets': {}}
    (OUT / 'expert_cpts.json').write_text(json.dumps(model_records(expert), indent=2), encoding='utf-8')
    lines = ['SMART HOME BAYESIAN NETWORK', f'Seed: {SEED}; nested dataset prefixes',
             'All CPTs and the full joint distribution sum to one.', '', 'Expert queries:']
    lines += [f'Q{i}: {value:.10f}' for i, value in enumerate(truth, 1)]
    means = {'MLE': [], 'BDeu': []}
    for size in SIZES:
        data = samples[:size]
        write_csv(OUT / f'data_{size}.csv', NODES, data)
        weather = {w: sum(row['W'] == w for row in data) for w in STATES['W']}
        combinations = [{'Weather': w, 'Occupancy': o,
                         'count': sum(row['W'] == w and row['O'] == o for row in data)}
                        for w in STATES['W'] for o in STATES['O']]
        evidence_counts = [sum(all(row[n] == s for n, s in evidence.items()) for row in data)
                           for _, _, evidence in QUERIES]
        entry = {'weather_counts': weather, 'weather_frequencies': {w: c / size for w, c in weather.items()},
                 'weather_occupancy': combinations, 'evidence_counts': evidence_counts}
        learned = {}
        for label, ess in (('MLE', 0), ('BDeu', 10)):
            model, unseen = learn_parameters(data, ess)
            values = query_results(model)
            errors = [abs(a - b) for a, b in zip(values, truth)]
            entry[label] = {'queries': values, 'absolute_errors': errors,
                            'mean_absolute_error': sum(errors) / 7,
                            'unseen_mle_configurations': unseen}
            means[label].append(sum(errors) / 7)
            learned[label] = model
            (OUT / f'cpts_{size}_{label.lower()}.json').write_text(
                json.dumps(model_records(model), indent=2), encoding='utf-8')
        comparisons = [{'Query': f'Q{i + 1}', 'Expert': truth[i],
                        'MLE': entry['MLE']['queries'][i], 'Bayesian': entry['BDeu']['queries'][i],
                        'AbsDiff_MLE': entry['MLE']['absolute_errors'][i],
                        'AbsDiff_Bayesian': entry['BDeu']['absolute_errors'][i]}
                       for i in range(7)]
        write_csv(OUT / f'comparison_{size}.csv', list(comparisons[0]), comparisons)
        ac_rows = [{'Weather': key[0], 'Occupancy': key[1],
                    'Expert_On': p[0], 'Expert_Off': p[1],
                    'MLE_On': learned['MLE']['A'][key][0], 'MLE_Off': learned['MLE']['A'][key][1],
                    'BDeu_On': learned['BDeu']['A'][key][0], 'BDeu_Off': learned['BDeu']['A'][key][1]}
                   for key, p in expert['A'].items()]
        write_csv(OUT / f'ac_cpt_{size}.csv', list(ac_rows[0]), ac_rows)
        write_csv(OUT / f'weather_occupancy_{size}.csv', list(combinations[0]), combinations)
        results['datasets'][str(size)] = entry
        lines += ['', f'N = {size}', f'Weather counts: {weather}',
                  f'Weather frequencies: {entry["weather_frequencies"]}',
                  'Weather / occupancy counts:']
        lines += [f'  {r["Weather"]:4} {r["Occupancy"]:4}: {r["count"]}' for r in combinations]
        lines += ['AC CPT: W O | Expert(On) MLE(On) BDeu(On)']
        lines += [f'  {r["Weather"]:4} {r["Occupancy"]:4} | {r["Expert_On"]:.6f} {r["MLE_On"]:.6f} {r["BDeu_On"]:.6f}' for r in ac_rows]
        lines += ['Query | Expert | MLE | Bayesian | |Diff| MLE | |Diff| Bayesian']
        lines += [f'{r["Query"]} | {r["Expert"]:.9f} | {r["MLE"]:.9f} | {r["Bayesian"]:.9f} | {r["AbsDiff_MLE"]:.9f} | {r["AbsDiff_Bayesian"]:.9f}' for r in comparisons]
        for label in means:
            lines.append(f'{label} mean absolute difference: {entry[label]["mean_absolute_error"]:.9f}')
        lines.append(f'Evidence counts Q1-Q7: {evidence_counts}')
    network_plot()
    fig, ax = plt.subplots(figsize=(8, 5))
    for label, values in means.items():
        ax.plot(SIZES, values, marker='o', label=label)
    ax.set(xlabel='Dataset size', ylabel='Mean absolute difference over Q1-Q7',
           title='Learned query probabilities versus expert model', xticks=SIZES)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / 'estimator_comparison.png', dpi=180)
    plt.close(fig)
    (OUT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    text = '\n'.join(lines) + '\n'
    (OUT / 'run_output.txt').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
