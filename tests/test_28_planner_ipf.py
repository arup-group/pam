import numpy as np
import pandas as pd
import pytest
from pam.planner import ipf


@pytest.fixture
def marginals():
    m = [np.array([20, 80]), np.array([60, 40]), np.array([30, 60, 10])]
    return m


@pytest.fixture
def zone_data():
    df = pd.DataFrame(
        {
            "zone": ["a", "b"],
            "subpopulation|rich": [30, 80],
            "subpopulation|medium": [0, 0],
            "subpopulation|poor": [70, 120],
            "age|yes": [60, 110],
            "age|no": [40, 90],
        }
    ).set_index("zone")
    return df


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


def test_ipf_warns_zero_cell_issue(marginals):
    X = np.zeros(tuple(map(len, marginals)))
    with pytest.warns(UserWarning):
        ipf.ipf(X, marginals, max_iterations=10)


def test_zone_data_preprocessing(zone_data):
    expected_encodings = {"subpopulation": ["rich", "medium", "poor"], "age": ["yes", "no"]}
    expected_marginals = {
        "a": [np.array([30, 0, 70]), np.array([60, 40])],
        "b": [np.array([80, 0, 120]), np.array([110, 90])],
    }
    encodings, marginals = ipf.prepare_zone_marginals(zone_data)
    assert encodings == expected_encodings
    for zone, m in marginals.items():
        for i, arr in enumerate(m):
            np.testing.assert_almost_equal(arr, expected_marginals[zone][i])


def test_encoded_population_sizes(population, zone_data):
    encodings, marginals = ipf.prepare_zone_marginals(zone_data)
    encoded_population = ipf.get_sample_pool(population, encodings)
    assert len(encoded_population[(0, 0)]) == 1  # rich-yes: chris
    # poor - no: fatema, fred, gerry
    assert len(encoded_population[(2, 1)]) == 3
    assert len(encoded_population[(0, 1)]) == 1  # rich, no: nick


def test_missing_category_in_population_raises_error(population, zone_data):
    with pytest.raises(ValueError):
        ipf.generate_population(population, zone_data)


def test_generate_fitted_population_matches_marginals(population, zone_data):
    population["B"]["gerry"].attributes["age"] = "yes"  # avoid zero-cell issue
    pop = ipf.generate_population(population, zone_data)

    # check totals for each zone and category
    for zone, irow in zone_data.iterrows():
        for col, v in irow.items():
            n = 0
            var, cl = col.split("|")
            for hid, pid, person in pop.people():
                if (person.attributes[var] == cl) and (person.attributes["hzone"] == zone):
                    n += 1
            assert n == v
