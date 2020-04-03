import os
import pytest
import pandas as pd
from datetime import datetime

from pam.core import Population, Activity, minutes_to_datetime


simple_plans_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_plans.csv")
)
simple_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_attributes.csv")
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


def test_agent_pid_5_not_start_from_home(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[2].people[5].activities]
    assert acts == ['work', 'home']


def test_agent_pid_6_not_return_home(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[3].people[6].activities]
    assert acts == ['home', 'work']


def test_agent_pid_7_not_start_and_return_home_night_worker(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[4].people[7].activities]
    assert acts == ['work', 'home', 'work']


def test_agent_pid_8_not_start_and_return_home_night_worker_complex_chain_type1(
        simple_plans, simple_attributes
):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[5].people[8].activities]
    assert acts == ['work', 'shop', 'home', 'work']


def test_agent_pid_9_not_start_and_return_home_night_worker_complex_chain_type2(
        simple_plans, simple_attributes
):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[6].people[9].activities]
    assert acts == ['work', 'shop', 'home', 'work']


def test_agent_pid_10_not_start_from_home_impossible_chain_type1(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[7].people[10].activities]
    assert acts == ['work', 'shop', 'home']


def test_agent_pid_11_not_start_from_home_impossible_chain_type2(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[8].people[11].activities]
    assert acts == ['work', 'shop', 'home']
