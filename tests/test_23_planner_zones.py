import numpy as np
import pytest
from pam.planner.zones import Zones


@pytest.fixture
def zones(data_zones):
    return Zones(data=data_zones)


def test_get_variable(zones):
    np.testing.assert_equal(zones.jobs, np.array([[100], [200]]))
    np.testing.assert_equal(zones["jobs"], zones.jobs)
