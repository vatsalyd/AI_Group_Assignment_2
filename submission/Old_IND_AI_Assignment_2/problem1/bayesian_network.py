from itertools import product
from math import isclose
import random

NODES = ('W', 'D', 'O', 'A', 'L', 'E')
STATES = {
    'W': ('Hot', 'Mild', 'Cold'), 'D': ('Weekday', 'Weekend'),
    'O': ('High', 'Low'), 'A': ('On', 'Off'),
    'L': ('Heavy', 'Light'), 'E': ('High', 'Low'),
}
PARENTS = {'W': (), 'D': (), 'O': ('D',), 'A': ('W', 'O'),
           'L': ('O',), 'E': ('A', 'L')}
QUERIES = (
    ('E', 'High', {}), ('E', 'High', {'W': 'Hot'}),
    ('E', 'High', {'D': 'Weekend'}),
    ('E', 'High', {'W': 'Cold', 'O': 'High'}),
    ('W', 'Hot', {'E': 'High'}), ('A', 'On', {'E': 'High'}),
    ('A', 'On', {'E': 'High', 'L': 'Heavy'}),
)


def binary(probability):
    return (probability, 1 - probability)


def expert_model():
    return {
        'W': {(): (0.5, 0.3, 0.2)}, 'D': {(): (0.7, 0.3)},
        'O': {('Weekday',): binary(0.45), ('Weekend',): binary(0.8)},
        'A': {key: binary(p) for key, p in {
            ('Hot', 'High'): 0.9, ('Hot', 'Low'): 0.6,
            ('Mild', 'High'): 0.4, ('Mild', 'Low'): 0.15,
            ('Cold', 'High'): 0.1, ('Cold', 'Low'): 0.05}.items()},
        'L': {('High',): binary(0.75), ('Low',): binary(0.35)},
        'E': {key: binary(p) for key, p in {
            ('On', 'Heavy'): 0.92, ('On', 'Light'): 0.68,
            ('Off', 'Heavy'): 0.55, ('Off', 'Light'): 0.12}.items()},
    }


def validate_model(model):
    for node in NODES:
        expected = set(product(*(STATES[p] for p in PARENTS[node])))
        assert set(model[node]) == expected, node
        for key, probabilities in model[node].items():
            assert len(probabilities) == len(STATES[node]), (node, key)
            assert all(0 <= p <= 1 for p in probabilities), (node, key)
            assert isclose(sum(probabilities), 1, abs_tol=1e-12), (node, key)


def joint_distribution(model):
    validate_model(model)
    rows = []
    for values in product(*(STATES[n] for n in NODES)):
        assignment = dict(zip(NODES, values))
        probability = 1.0
        for node in NODES:
            key = tuple(assignment[p] for p in PARENTS[node])
            probability *= model[node][key][STATES[node].index(assignment[node])]
        rows.append((assignment, probability))
    assert isclose(sum(p for _, p in rows), 1, abs_tol=1e-12)
    return rows


def probability(rows, event, evidence=None):
    evidence = evidence or {}
    for node, state in {**event, **evidence}.items():
        if node not in STATES or state not in STATES[node]:
            raise ValueError(f'Invalid assignment: {node}={state}')
    denominator = numerator = 0.0
    for assignment, mass in rows:
        if all(assignment[n] == s for n, s in evidence.items()):
            denominator += mass
            if all(assignment[n] == s for n, s in event.items()):
                numerator += mass
    if denominator == 0:
        raise ValueError('Evidence has zero probability')
    return numerator / denominator


def query_results(model):
    rows = joint_distribution(model)
    return [probability(rows, {node: state}, evidence)
            for node, state, evidence in QUERIES]


def ancestral_sample(model, size, seed=2026):
    validate_model(model)
    rng = random.Random(seed)
    samples = []
    for _ in range(size):
        assignment = {}
        for node in NODES:
            key = tuple(assignment[p] for p in PARENTS[node])
            draw = rng.random()
            cumulative = 0.0
            for state, mass in zip(STATES[node], model[node][key]):
                cumulative += mass
                if draw < cumulative:
                    assignment[node] = state
                    break
            else:
                assignment[node] = STATES[node][-1]
        samples.append(assignment)
    return samples


def learn_parameters(samples, equivalent_sample_size=0):
    if equivalent_sample_size < 0 or not samples:
        raise ValueError('Use nonempty data and nonnegative equivalent sample size')
    model = {}
    unseen = []
    for node in NODES:
        configurations = list(product(*(STATES[p] for p in PARENTS[node])))
        r, q = len(STATES[node]), len(configurations)
        counts = {key: [0] * r for key in configurations}
        for row in samples:
            key = tuple(row[p] for p in PARENTS[node])
            counts[key][STATES[node].index(row[node])] += 1
        model[node] = {}
        for key, values in counts.items():
            total = sum(values)
            if total == 0 and equivalent_sample_size == 0:
                unseen.append((node, key))
                model[node][key] = tuple([1 / r] * r)
            else:
                model[node][key] = tuple(
                    (count + equivalent_sample_size / (r * q)) /
                    (total + equivalent_sample_size / q) for count in values)
    validate_model(model)
    return model, unseen
