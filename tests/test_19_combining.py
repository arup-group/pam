import pytest
import os
import geopandas as gp
from shapely.geometry import Point, Polygon
from copy import deepcopy

from pam.core import Population, Household, Person
from pam.activity import Activity, Leg, Plan
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam.operations import combine
from pam import read


@pytest.fixture
def path_population_A():
    return os.path.join('tests', 'test_data', 'test_matsim_population_A.xml')


@pytest.fixture
def path_population_B():
    return os.path.join('tests', 'test_data', 'test_matsim_population_B.xml')


def test_combined_length(path_population_A, path_population_B):
    """ Combined population size equates to the sum of the individual populations """
    combined_pop = combine.pop_combine(
        [path_population_A, path_population_B],
        matsim_version=12,
        )
    assert len(combined_pop) == 6


# def test_combine_duplicates(test_population_1)
#     """ Test that the same ID's can't be repeated """
#     combined_pop = combine.pop_combine(test_population_1, test_population_1)
#     assert (no duplicate hid's)



# def test_crop_xml(path_test_plan, path_boundary, tmp_path):
#     """ Crop and export an xml population """
#     path_output_dir = str(tmp_path)
#     cropping.crop_xml(
#         path_test_plan,
#         path_boundary,
#         path_output_dir
#     )
#     assert os.path.exists(os.path.join(path_output_dir, 'plans.xml'))