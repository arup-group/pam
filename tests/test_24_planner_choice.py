import pytest
from tests.test_22_planner_od import data_od, labels, od
from tests.test_23_planner_zones import data_zones
from pam.planner.choice import ChoiceModel, ChoiceMNL
import os
from pam.read import read_matsim
from pam.planner.od import OD

test_plans = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 "test_data/test_matsim_plansv12.xml")
)


@pytest.fixture
def population():
    population = read_matsim(test_plans, version=12)
    for hid, pid, person in population.people():
        person.home.area = 'h'
        for act in person.activities:
            act.location.area = 'h'
    return population


@pytest.fixture
def choice_model(population, od, data_zones):
    return ChoiceModel(population, od, data_zones)


def test_zones_are_aligned(population, od, data_zones):
    choice_model = ChoiceModel(population, od, data_zones.loc[['b', 'a']])
    zones_destination = choice_model.od.labels.destination_zones
    zones_index = list(choice_model.zones.index)
    assert zones_destination == zones_index

def test_utility_calculation(choice_model):
    asc = 0.1
    u = """asc + beta_time * od.car.time * leg.mode==car"""