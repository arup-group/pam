import pytest

from pam.samplers import attributes


@pytest.fixture
def michael():

    return {
        'age': 16,
        'agebin': 'younger',
        'gender': 'male'
    }


@pytest.fixture
def kasia():

    return {
        'age': 96,
        'agebin': 'older',
        'gender': 'female'
    }


@pytest.fixture
def fred():

    return {
        'age': -3,
        'agebin': None,
        'gender': 1
    }


@pytest.fixture
def bins():

    return {
        (0,50): 'younger',
        (51,100): 'older'
    }


@pytest.fixture
def cat_joint_distribution():

    mapping = ['agebin', 'gender']
    distribution = {
        'younger': {'male': 0, 'female': 0},
        'older': {'male': 0, 'female': 1}
    }
    return mapping, distribution


def test_bin_integer_transformer(michael, bins):
    assert attributes.bin_integer_transformer(michael, 'age', bins) == 'younger'


def test_bin_integer_transformer_missing(fred, bins):
    assert attributes.bin_integer_transformer(fred, 'age', bins) is None


def test_discrete_joint_distribution_sampler_michael(michael, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(michael, mapping, dist) == False


def test_discrete_joint_distribution_sampler_kasia(kasia, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(kasia, mapping, dist) == True