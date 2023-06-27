import pytest
import numpy as np
import random
import os
from pam.read import read_matsim
from pam.activity import Leg
from pam.operations.cropping import link_population

from pam.planner.utils_planner import (
    calculate_mnl_probabilities,
    sample_weighted,
    get_trip_chains,
    apply_mode_to_home_chain,
    get_validate,
)

test_plans_experienced = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_experienced_plans_v12.xml")
)


@pytest.fixture
def population_experienced():
    population = read_matsim(test_plans_experienced, version=12)
    return population


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
    choices = np.array([10] * n)
    probs = calculate_mnl_probabilities(choices)
    assert (probs == (1 / n)).all()


def test_get_home_trip_chains(population_experienced):
    person = population_experienced["agent_1"]["agent_1"]
    person.plan.day[12].act = "home"
    chains = get_trip_chains(person.plan)
    assert len(chains) == 2
    assert chains[0][-1] == person.plan.day[12]
    assert chains[1][0] == person.plan.day[12]


def test_apply_mode_to_chain(population_experienced):
    link_population(population_experienced)
    person = population_experienced["agent_1"]["agent_1"]
    person.plan.day[12].act = "home"
    chains = get_trip_chains(person.plan)
    apply_mode_to_home_chain(person.plan.day[10], "gondola")

    # mode is applied to all legs in the chain
    legs = [elem for elem in chains[0] if isinstance(elem, Leg)]
    assert all([leg.mode == "gondola" for leg in legs])

    # ..but not to the next trip chain
    legs = [elem for elem in chains[1] if isinstance(elem, Leg)]
    assert all([leg.mode != "gondola" for leg in legs])


def test_nonset_attribute_raises_error():
    class A:
        a = "b"
        b = None

    a = A()
    with pytest.raises(ValueError):
        get_validate(a, "b")
