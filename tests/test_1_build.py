import os
import pytest
import pandas as pd

from pam.core import Population, Activity


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


def test_load(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    assert population


def test_agent_pid_0_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[0].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work', 'home']


def test_agent_pid_1_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[1].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work', 'home', 'other', 'home']


def test_agent_pid_2_simple_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[0].people[2].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work', 'home', 'work', 'home']


def test_agent_pid_3_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[1].people[3].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work', 'shop', 'work', 'home']


def test_agent_pid_4_complex_tour(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[1].people[4].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work', 'work', 'work', 'work', 'home']


def test_agent_pid_5_not_start_from_home(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[2].people[5].plan if isinstance(a, Activity)]
    assert acts == ['work', 'home']


def test_agent_pid_6_not_return_home(simple_plans, simple_attributes):
    population = Population()
    population.load(simple_plans, simple_attributes)
    acts = [a.act for a in population.households[3].people[6].plan if isinstance(a, Activity)]
    assert acts == ['home', 'work']
