import os
import pytest
import pandas as pd

from pam.parse import load_travel_diary
from .fixtures import person_crop_last_act, person_crop_last_leg

test_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_travel_diaries.csv")
)
test_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_persons_data.csv")
)


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


def test_agent_pid_0_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['0'].people['0'].activities]
    assert acts == ['home', 'work', 'home']


def test_agent_pid_1_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['0'].people['1'].activities]
    assert acts == ['home', 'work', 'home', 'other', 'home']


def test_agent_pid_2_simple_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['0'].people['2'].activities]
    assert acts == ['home', 'work', 'home', 'work', 'home']


def test_agent_pid_3_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['1'].people['3'].activities]
    print(acts)
    assert acts == ['home', 'work', 'shop', 'work', 'home']


def test_agent_pid_4_complex_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['1'].people['4'].activities]
    assert acts == ['home', 'work', 'work', 'work', 'work', 'home']


def test_crop_last_act(person_crop_last_act):
    person_crop_last_act.plan.crop()
    assert person_crop_last_act.has_valid_plan


def test_crop_last_leg(person_crop_last_leg):
    person_crop_last_leg.plan.crop()
    assert person_crop_last_leg.has_valid_plan


def test_infer_home_activity_idxs_simple(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households['0'].people['2']
    assert person.plan.infer_activity_idxs(target=person.home) == {0,4,8}


def test_infer_home_activity_idxs_mid_plan(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households['6'].people['9']
    assert person.plan.infer_activity_idxs(target=person.home) == {4}


def test_infer_home_activity_idxs_complex(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households['8'].people['11']
    assert person.plan.infer_activity_idxs(target=person.home) == {4}


def test_infer_home_activity_idxs_missing(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households['18'].people['21']
    assert person.plan.infer_activity_idxs(target=person.home) == {0}


def test_infer_home_activity_idxs_longest(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    person = population.households['19'].people['22']
    assert person.plan.infer_activity_idxs(target=person.home) == {0,6}
