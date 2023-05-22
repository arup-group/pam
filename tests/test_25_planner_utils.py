import pytest
import numpy as np
import random
from pam.planner.utils_planner import calculate_mnl_probabilities, \
    sample_weighted


def test_weighted_sampling_zero_weight():
    choices = np.array([0, 0, 1])
    assert sample_weighted(choices) == 2


def test_weighted_sampling_seed_results():
    choices = np.array([10, 3, 9, 0, 11, 2])
    random.seed(10)
    assert sample_weighted(choices) == 2


def test_mnl_probabilities_add_up():
    choices = np.array([10, 3, 9, 0, 11, 2])
    probs = calculate_mnl_probabilities(choices)
    assert round(probs.sum(), 4) == 1


def test_mnl_equal_weights_equal_probs():
    n = 10
    choices = np.array([10]*n)
    probs = calculate_mnl_probabilities(choices)
    assert (probs==(1/n)).all()

