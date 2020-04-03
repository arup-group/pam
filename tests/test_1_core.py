import os
import pytest
import pandas as pd
from datetime import datetime

from pam.core import Population, Activity, minutes_to_datetime


simple_plans_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_travel_diaries.csv")
)
simple_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_persons_data.csv")
)


@pytest.fixture
def simple_plans():
    df = pd.read_csv(simple_plans_path)
    assert not df.empty
    return df


@pytest.fixture
def simple_attributes():
    df = pd.read_csv(simple_attributes_path)
    assert not df.empty
    return df


testdata = [
    (0, datetime(2020, 4, 2, 0, 0)),
    (30, datetime(2020, 4, 2, 0, 30)),
    (300, datetime(2020, 4, 2, 5, 0)),
    (330, datetime(2020, 4, 2, 5, 30)),
]


@pytest.mark.parametrize("m,expected", testdata)
def test_minutes_to_dt(m, expected):
    assert minutes_to_datetime(m) == expected


def test_load(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    assert population


def test_agent_pid_0_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[0].activities]
    assert acts == ['home', 'work', 'home']


def test_agent_pid_1_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[1].activities]
    assert acts == ['home', 'work', 'home', 'other', 'home']


def test_agent_pid_2_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[2].activities]
    assert acts == ['home', 'work', 'home', 'work', 'home']


def test_agent_pid_3_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[1].people[3].activities]
    assert acts == ['home', 'work', 'shop', 'work', 'home']


def test_agent_pid_4_complex_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[1].people[4].activities]
    assert acts == ['home', 'work', 'work', 'work', 'work', 'home']
