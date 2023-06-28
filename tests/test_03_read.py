import os
from datetime import datetime

import pandas as pd
import pytest

from pam.core import Household, Population
from pam.read import load_pickle, load_travel_diary
from pam.utils import parse_time

test_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_travel_diaries.csv")
)
test_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_persons_data.csv")
)


testdata = [
    (0, datetime(1900, 1, 1, 0, 0)),
    (1, datetime(1900, 1, 1, 0, 1)),
    (60, datetime(1900, 1, 1, 1, 0)),
    ("1900-01-01 13:00:00", datetime(1900, 1, 1, 13, 0)),
]


@pytest.mark.parametrize("a,expected", testdata)
def test_time_parse(a, expected):
    assert parse_time(a) == expected


@pytest.fixture
def test_trips():
    df = pd.read_csv(test_trips_path)
    assert not df.empty
    return df


@pytest.fixture
def test_attributes():
    df = pd.read_csv(test_attributes_path)
    assert not df.empty
    return df


def test_load(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    assert population


def test_load_from_paths():
    population = load_travel_diary(test_trips_path, test_attributes_path)
    assert population


def test_agent_pid_0_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[0].people[0].activities]
    assert acts == ["home", "work", "home"]


def test_agent_pid_1_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[0].people[1].activities]
    assert acts == ["home", "work", "home", "other", "home"]


def test_agent_pid_2_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[0].people[2].activities]
    assert acts == ["home", "work", "home", "work", "home"]


def test_agent_pid_3_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[1].people[3].activities]
    assert acts == ["home", "work", "shop", "work", "home"]


def test_agent_pid_4_complex_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[1].people[4].activities]
    assert acts == ["home", "work", "work", "work", "work", "home"]


def test_crop_last_act(person_crop_last_act):
    person_crop_last_act.plan.crop()
    assert person_crop_last_act.has_valid_plan


def test_crop_last_leg(person_crop_last_leg):
    person_crop_last_leg.plan.crop()
    assert person_crop_last_leg.has_valid_plan


def test_infer_home_activity_idxs_simple(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households[0].people[2]
    assert person.plan.infer_activity_idxs(target=person.home) == {0, 4, 8}


def test_infer_home_activity_idxs_mid_plan(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households[6].people[9]
    assert person.plan.infer_activity_idxs(target=person.home) == {4}


def test_infer_home_activity_idxs_complex(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households[8].people[11]
    assert person.plan.infer_activity_idxs(target=person.home) == {4}


def test_infer_home_activity_idxs_missing(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households[18].people[21]
    assert person.plan.infer_activity_idxs(target=person.home) == {0}


def test_infer_home_activity_idxs_longest(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households[19].people[22]
    assert person.plan.infer_activity_idxs(target=person.home) == {0, 6}


def test_pickle_population(person_crop_last_act, tmpdir):
    population = Population()
    hh = Household("1")
    hh.add(person_crop_last_act)
    population.add(hh)
    path = os.path.join(tmpdir, "test.pkl")
    population.pickle(path)
    assert os.path.exists(path)


def test_load_pickle_population(person_crop_last_act, tmpdir):
    population = Population()
    hh = Household("1")
    hh.add(person_crop_last_act)
    population.add(hh)
    path = os.path.join(tmpdir, "test.pkl")
    population.pickle(path)
    loaded = load_pickle(path)
    assert loaded.households
    assert list(loaded.households["1"].people) == list(population.households["1"].people)


def test_pickle_household(person_crop_last_act, tmpdir):
    hh = Household("1")
    hh.add(person_crop_last_act)
    path = os.path.join(tmpdir, "test.pkl")
    hh.pickle(path)
    assert os.path.exists(path)


def test_load_pickle_household(person_crop_last_act, tmpdir):
    hh = Household("1")
    hh.add(person_crop_last_act)
    path = os.path.join(tmpdir, "test.pkl")
    hh.pickle(path)
    loaded = load_pickle(path)
    assert loaded.people
    assert list(loaded.people["1"].attributes) == list(hh.people["1"].attributes)


def test_pickle_person(person_crop_last_act, tmpdir):
    path = os.path.join(tmpdir, "test.pkl")
    person_crop_last_act.pickle(path)
    assert os.path.exists(path)


def test_load_pickle_person(person_crop_last_act, tmpdir):
    path = os.path.join(tmpdir, "test.pkl")
    person_crop_last_act.pickle(path)
    loaded = load_pickle(path)
    assert loaded.plan.day
    assert [a.act for a in loaded.plan.activities] == [
        a.act for a in person_crop_last_act.plan.activities
    ]
