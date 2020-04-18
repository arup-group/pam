import os
import pytest
import pandas as pd

from pam.parse import load_travel_diary

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
    assert acts == ['home', 'work', 'shop', 'work', 'home']


def test_agent_pid_4_complex_tour(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households['1'].people['4'].activities]
    assert acts == ['home', 'work', 'work', 'work', 'work', 'home']
