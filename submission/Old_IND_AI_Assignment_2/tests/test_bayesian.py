import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'problem1'))
from bayesian_network import (
    ancestral_sample, expert_model, joint_distribution, learn_parameters,
    probability, query_results, validate_model,
)


class BayesianTests(unittest.TestCase):
    def setUp(self):
        self.model = expert_model()
        self.joint = joint_distribution(self.model)

    def test_manual_marginal_and_conditional(self):
        p_high_o = 0.7 * 0.45 + 0.3 * 0.8
        high_o = 0.4425 + 0.4175 * 0.59
        low_o = 0.2705 + 0.4935 * 0.355
        expected = p_high_o * high_o + (1 - p_high_o) * low_o
        self.assertAlmostEqual(query_results(self.model)[0], expected, places=12)
        self.assertAlmostEqual(query_results(self.model)[3], 0.48425, places=12)

    def test_independence_and_explaining_away(self):
        self.assertAlmostEqual(probability(self.joint, {'W': 'Hot'}, {'D': 'Weekend'}), 0.5)
        self.assertAlmostEqual(probability(self.joint, {'W': 'Hot'}, {'O': 'High', 'L': 'Heavy'}), 0.5)
        queries = query_results(self.model)
        self.assertGreater(queries[5], queries[6])
        self.assertNotAlmostEqual(queries[4], probability(self.joint, {'W': 'Hot'}, {'E': 'High', 'D': 'Weekend'}))

    def test_sampler_reproducibility_and_learning(self):
        data = ancestral_sample(self.model, 500)
        self.assertEqual(data, ancestral_sample(self.model, 500))
        mle, unseen = learn_parameters(data)
        bayes, _ = learn_parameters(data, 10)
        self.assertFalse(unseen)
        hot = sum(r['W'] == 'Hot' for r in data)
        self.assertAlmostEqual(mle['W'][()][0], hot / 500)
        self.assertAlmostEqual(bayes['W'][()][0], (hot + 10 / 3) / 510)
        validate_model(mle)
        validate_model(bayes)

    def test_invalid_model_and_impossible_evidence(self):
        self.model['W'][()] = (1, 0, 0)
        joint = joint_distribution(self.model)
        with self.assertRaises(ValueError):
            probability(joint, {'E': 'High'}, {'W': 'Cold'})
        self.model['W'][()] = (0.5, 0.3, 0.3)
        with self.assertRaises(AssertionError):
            validate_model(self.model)


if __name__ == '__main__':
    unittest.main()
