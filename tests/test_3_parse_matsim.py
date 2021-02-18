import os
import pytest

from pam.read import load_attributes_map, read_matsim


test_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plans.xml")
)
test_tripsv12_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plansv12.xml")
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


def test_parsing_complex_person_results_in_valid_pt_leg():
    population = read_matsim(test_trips_path, test_attributes_path)
    person = population['census_1']['census_1']

    pt_leg = person.plan.day[5]
    assert pt_leg.mode == 'pt'
    assert pt_leg.service_id == '25239'
    assert pt_leg.route_id == 'VJ307b99b535bf55bc9d62b5475e5edf0d37176bcf'
    assert pt_leg.o_stop == '9100ROMFORD.link:25821'
    assert pt_leg.d_stop == '9100UPMNSP6.link:302438'


def test_parsing_person_with_network_route():
    population = read_matsim(test_trips_path)
    person = population['census_2']['census_2']

    bike_trip = person.plan.day[1]
    assert bike_trip.mode == 'bike'
    assert bike_trip.network_route == ['link_1', 'link_2', 'link_3']
    assert bike_trip.service_id is None
    assert bike_trip.route_id is None
    assert bike_trip.o_stop is None
    assert bike_trip.d_stop is None


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


# v12
def test_parse_v12_matsim():
   population = read_matsim(test_tripsv12_path, version=12)
   person = population['chris']['chris']
   assert person.has_valid_plan
   assert person.attributes == {'subpopulation': 'rich', 'age': 'yes'}


def test_fail_v12_plus_attributes():
    with pytest.raises(UserWarning):
        population = read_matsim(test_tripsv12_path, attributes_path='fake', version=12)


def test_fail_bad_version():
    with pytest.raises(UserWarning):
        population = read_matsim(test_tripsv12_path, version=1)
