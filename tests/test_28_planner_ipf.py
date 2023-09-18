import numpy as np
import pytest

from pam.planner.ipf import ipf


@pytest.fixture
def marginals():
    m = [np.array([20, 80]), np.array([60, 40]), np.array([30, 60, 10])]
    return m


def test_random_seed_matches_marginals(marginals):
    X = np.zeros(tuple(map(len, marginals))) + 0.001
    fitted = ipf(X, marginals, max_iterations=10)
    np.testing.assert_almost_equal(fitted.sum((1, 2)), marginals[0])


def test_ipf_maxes_patience_out():
    pass
