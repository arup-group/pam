import pytest
from lxml import etree as et
from pam.activity import Plan
from pam.read import (
    get_attributes_from_person,
    load_attributes_map,
    parse_veh_attribute,
    read_matsim,
    stream_matsim_persons,
)

test_trips_path = pytest.test_data_dir / "test_matsim_plans.xml"
test_tripsv12_path = pytest.test_data_dir / "test_matsim_plansv12.xml"
test_attributes_path = pytest.test_data_dir / "test_matsim_attributes.xml"


def test_load_attributes_map():
    attributes_map = load_attributes_map(test_attributes_path)
    assert isinstance(attributes_map, dict)
    assert attributes_map["census_0"] == {
        "source": "census_2016",
        "subpopulation": "default",
        "gender": "female",
        "activity": "work",
        "mode": "pt",
        "occupation": "white",
        "income": "low",
    }


def test_parse_simple_matsim():
    population = read_matsim(test_trips_path, test_attributes_path, version=11)
    person = population["census_0"]["census_0"]
    assert person.has_valid_plan


def test_parse_complex_matsim():
    population = read_matsim(test_trips_path, test_attributes_path, version=11)
    person = population["census_1"]["census_1"]
    assert person.has_valid_plan


def test_parsing_complex_person_results_in_valid_pt_leg():
    population = read_matsim(test_trips_path, test_attributes_path, version=11)
    person = population["census_1"]["census_1"]

    pt_leg = person.plan.day[5]
    assert pt_leg.mode == "pt"
    assert pt_leg.route.exists
    assert pt_leg.route.is_transit
    assert not pt_leg.route.is_routed
    assert not pt_leg.route.is_teleported
    assert pt_leg.route.transit.get("transitLineId") == "25239"
    assert (
        pt_leg.route.transit.get("transitRouteId") == "VJ307b99b535bf55bc9d62b5475e5edf0d37176bcf"
    )
    assert pt_leg.route.transit.get("accessFacilityId") == "9100ROMFORD.link:25821"
    assert pt_leg.route.transit.get("egressFacilityId") == "9100UPMNSP6.link:302438"
    assert pt_leg.route.network_route == []


def test_parsing_person_with_network_route():
    population = read_matsim(test_trips_path, version=11)
    person = population["census_2"]["census_2"]

    bike_trip = person.plan.day[1]
    assert bike_trip.mode == "bike"
    assert bike_trip.route.exists
    assert bike_trip.route.is_routed
    assert not bike_trip.route.is_transit
    assert not bike_trip.route.is_teleported
    assert bike_trip.route.network_route == ["link_1", "link_2", "link_3"]


def test_remove_pt_interactions():
    population = read_matsim(test_trips_path, test_attributes_path, version=11)
    person = population["census_1"]["census_1"]
    person.plan.simplify_pt_trips()
    assert "pt interaction" not in [a.act for a in person.activities]
    assert person.has_valid_plan


test_bad_trips_path = pytest.test_data_dir / "test_matsim_bad_plan.xml"
test_bad_attributes_path = pytest.test_data_dir / "test_matsim_bad_attributes.xml"


def test_read_plan_with_negative_durations():
    population = read_matsim(test_bad_trips_path, test_bad_attributes_path, version=11)
    assert population["test"]["test"].plan.is_valid


# v12
def test_parse_v12_matsim():
    population = read_matsim(test_tripsv12_path, version=12)
    person = population["chris"]["chris"]
    assert person.has_valid_plan
    assert person.attributes == {
        "subpopulation": "rich",
        "age": "yes",
        "hid": "A",
        "vehicles": {"car": "chris"},
    }
    legs = list(person.plan.legs)
    assert legs[0].mode == "car"
    assert legs[1].mode == "car"
    assert legs[1].distance == 10300
    assert legs[1].service_id is None
    assert legs[1].route_id is None
    assert legs[1].o_stop is None
    assert legs[1].d_stop is None
    assert legs[1].network_route == ["3-4", "4-3", "3-2", "2-1", "1-2"]


def test_parse_v12_matsim_with_hh_ids():
    population = read_matsim(test_tripsv12_path, version=12, household_key="hid")
    person = population["A"]["chris"]
    assert person.has_valid_plan
    assert person.attributes == {
        "subpopulation": "rich",
        "age": "yes",
        "hid": "A",
        "vehicles": {"car": "chris"},
    }
    legs = list(person.plan.legs)
    assert legs[0].mode == "car"
    assert legs[1].mode == "car"
    assert legs[1].distance == 10300
    assert legs[1].service_id is None
    assert legs[1].route_id is None
    assert legs[1].o_stop is None
    assert legs[1].d_stop is None
    assert legs[1].network_route == ["3-4", "4-3", "3-2", "2-1", "1-2"]


def test_parse_transit_v12_matsim():
    population = read_matsim(test_tripsv12_path, version=12)
    person = population["fred"]["fred"]
    assert person.has_valid_plan
    assert person.attributes == {"subpopulation": "poor", "age": "no", "hid": "B"}
    legs = list(person.plan.legs)
    assert legs[0].mode == "walk"
    assert legs[1].mode == "bus"
    assert legs[1].distance == 10100
    assert legs[1].route.transit.get("transitLineId") == "city_line"
    assert legs[1].route.transit.get("transitRouteId") == "work_bound"
    assert legs[1].route.transit.get("accessFacilityId") == "home_stop_out"
    assert legs[1].route.transit.get("egressFacilityId") == "work_stop_in"
    assert legs[1].route.network_route == []


def test_fail_v12_plus_attributes():
    with pytest.raises(UserWarning):
        read_matsim(test_tripsv12_path, attributes_path="fake", version=12)


def test_fail_bad_version():
    with pytest.raises(UserWarning):
        read_matsim(test_tripsv12_path, version=1)


def test_parse_simple_matsim_non_selected():
    population = read_matsim(
        test_trips_path, test_attributes_path, keep_non_selected=True, version=11
    )
    person1 = population["census_1"]["census_1"]
    person2 = population["census_2"]["census_2"]
    assert person1.has_valid_plan
    assert person2.has_valid_plan
    assert len(person1.plans_non_selected) == 1
    assert len(person2.plans_non_selected) == 0
    assert isinstance(person1.plans_non_selected[0], Plan)
    assert person1.plans_non_selected[0].score == 0


# test stream matsim


def test_stream_transit_v12_matsim():
    population = {person.pid: person for person in stream_matsim_persons(test_tripsv12_path)}
    person = population["fred"]
    assert person.has_valid_plan
    assert person.attributes == {"subpopulation": "poor", "age": "no", "hid": "B"}
    legs = list(person.plan.legs)
    assert legs[0].mode == "walk"
    assert legs[1].mode == "bus"
    assert legs[1].distance == 10100
    assert legs[1].route.transit.get("transitLineId") == "city_line"
    assert legs[1].route.transit.get("transitRouteId") == "work_bound"
    assert legs[1].route.transit.get("accessFacilityId") == "home_stop_out"
    assert legs[1].route.transit.get("egressFacilityId") == "work_stop_in"
    assert legs[1].route.network_route == []


def test_parse_veh_attribute():
    assert parse_veh_attribute('{"car":"chris"}') == {"car": "chris"}


def test_get_attributes_from_person():
    text = """<person id="chris">
    <attributes>
        <attribute name="hid" class="java.lang.String">A</attribute>
        <attribute name="subpopulation" class="java.lang.String">rich</attribute>
        <attribute name="age" class="java.lang.String">yes</attribute>
        <attribute name="vehicles" class="org.matsim.vehicles.PersonVehicles">{"car":"chris"}</attribute>
    </attributes>
</person>"""
    elem = et.fromstring(text)
    pid, attributes = get_attributes_from_person(elem)
    assert pid == "chris"
    assert attributes["hid"] == "A"
    assert attributes["vehicles"] == {"car": "chris"}


def test_get_float_attribute_from_person():
    text = """<person id="chris">
        <attributes>
            <attribute name="age" class="java.lang.Double">10.0</attribute>
        </attributes>
    </person>"""
    elem = et.fromstring(text)
    pid, attributes = get_attributes_from_person(elem)
    assert isinstance(attributes["age"], float)
