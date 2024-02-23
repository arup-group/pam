import os

import pytest
from pam.operations import combine


@pytest.fixture
def path_population_A():
    return os.path.join("tests", "test_data", "test_matsim_population_A.xml")


@pytest.fixture
def path_population_B():
    return os.path.join("tests", "test_data", "test_matsim_population_B.xml")


def test_combined_length(path_population_A, path_population_B):
    """Combined population size equates to the sum of the individual populations."""
    combined_pop = combine.pop_combine([path_population_A, path_population_B], matsim_version=12)
    assert len(combined_pop) == 6
