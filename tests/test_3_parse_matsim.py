import os
import pytest

from pam.read import load_attributes_map, read_matsim


test_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plans.xml")
)
test_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_attributes.xml")
)


def test_load_attributes_map():

    attributes_map = load_attributes_map(test_attributes_path)
    assert isinstance(attributes_map, dict)
    assert attributes_map['census_0'] == {
        'source': 'census_2016',
        'subpopulation': 'default',
        'gender': 'female',
        'activity': 'work',
        'mode': 'pt',
        'occupation': 'white',
        'income': 'low'
        }


def test_parse_simple_matsim():
   population = read_matsim(test_trips_path, test_attributes_path)
   person = population['census_0']['census_0']
   
   assert person.has_valid_plan


def test_parse_complex_matsim():
   population = read_matsim(test_trips_path, test_attributes_path)
   person = population['census_1']['census_1']
   assert person.has_valid_plan


def test_remove_pt_interactions():
    population = read_matsim(test_trips_path, test_attributes_path)
    person = population['census_1']['census_1']
    person.plan.simplify_pt_trips()
    assert 'pt interaction' not in [a.act for a in person.activities]
    assert person.has_valid_plan


test_bad_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_bad_plan.xml")
)
test_bad_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_bad_attributes.xml")
)


def test_read_plan_with_negative_durations():
    population = read_matsim(test_bad_trips_path, test_bad_attributes_path)
    population['test']['test'].print()
