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


def test_get_variable(zones):
    np.testing.assert_equal(zones.jobs, np.array([[100], [200]]))
    np.testing.assert_equal(zones['jobs'], zones.jobs)