import numpy as np
import pytest

from pam.planner import ipf


@pytest.fixture
def marginals():
    m = [np.array([20, 80]), np.array([60, 40]), np.array([30, 60, 10])]
    return m


def test_random_seed_matches_marginals(marginals):
    X = np.zeros(tuple(map(len, marginals))) + 0.001
    fitted = ipf.ipf(X, marginals, max_iterations=10)
    np.testing.assert_almost_equal(fitted.sum((1, 2)), marginals[0])
    np.testing.assert_almost_equal(fitted.sum((0, 2)), marginals[1])
    np.testing.assert_almost_equal(fitted.sum((0, 1)), marginals[2])


def test_ipf_maxes_patience_out(mocker):
    mocker.patch.object(ipf, "get_scaling_factor", return_value=np.ones((2, 2)) * 2)
    ipf.ipf(np.zeros((2, 2)) + 0.1, np.ones((2, 2)), max_iterations=0)
    # only called once for each dimension at the start
    assert ipf.get_scaling_factor.call_count == 2


def test_ipf_matrix_retains_shape(marginals):
    X = np.zeros(tuple(map(len, marginals))) + 0.001
    fitted = ipf.ipf(X, marginals, max_iterations=10)
    assert fitted.shape == X.shape


def test_ipf_raises_zero_cell_problem(marginals):
    X = np.zeros(tuple(map(len, marginals)))
    with pytest.warns(UserWarning):
        ipf.ipf(X, marginals, max_iterations=10)
