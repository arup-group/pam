import pytest
from pam.planner.zones import Zones
import pandas as pd
import numpy as np


@pytest.fixture
def data_zones():
    df = pd.DataFrame(
        {
            'zone': ['a', 'b'],
            'jobs': [100, 200],
            'schools': [3, 1]
        }
    ).set_index('zone')
    return df

@pytest.fixture
def zones(data_zones):
    return Zones(data=data_zones)

def test_get_zone_data(data_zones):
    np.testing.assert_equal(data_zones.loc['b'].values, np.array([200, 1]))


def test_get_variable_data(data_zones):
    np.testing.assert_equal(data_zones['jobs'], np.array([100, 200]))


def test_get_values(data_zones):
    assert data_zones.loc['b', 'jobs'] == 200
    assert data_zones.loc['b']['jobs'] == 200

def test_get_variable(zones):
    np.testing.assert_equal(zones.jobs, np.array([100, 200]))