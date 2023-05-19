import pytest
import numpy as np
from tests.test_22_planner_od import data_od, labels, od
from tests.test_23_planner_zones import data_zones
from pam.planner.choice import ChoiceModel, ChoiceMNL, ChoiceSet
from pam.planner.utils_planner import sample_weighted
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
        for act in person.activities:
            act.location.area = 'a'
    return population


@pytest.fixture
def choice_model(population, od, data_zones) -> ChoiceModel:
    return ChoiceModel(population, od, data_zones)

@pytest.fixture
def choice_model_mnl(population, od, data_zones) -> ChoiceModel:
    return ChoiceMNL(population, od, data_zones)


def test_zones_are_aligned(population, od, data_zones):
    choice_model = ChoiceModel(population, od, data_zones.loc[['b', 'a']])
    zones_destination = choice_model.od.labels.destination_zones
    zones_index = list(choice_model.zones.index)
    assert zones_destination == zones_index

@pytest.mark.parametrize('var', ['time', 'distance'])
@pytest.mark.parametrize('zone', ['a', 'b'])
def test_choice_set_reads_od_correctly(choice_model, var, zone):
    choice_model.configure(
        u = f"""1 / od['{var}', '{zone}']""",
        scope = """act.act=='work'"""
    )
    choice_set = choice_model.get_choice_set()
    assert choice_set.choice_labels == [
        ('a', 'car'), ('a', 'bus'), ('b', 'car'), ('b', 'bus') 
    ]
    for choice in choice_set.u_choices:
        np.testing.assert_array_equal(
            choice, 
            1 / choice_model.od[var, zone].flatten()
        )

def test_list_parameters_correspond_to_modes(choice_model):
    """
    When utility parameters are passed as a list, 
        they should be applied to each respective mode.
    """
    asc = [0, 10] # 0 should be applied to car, 10 to bus
    choice_model.configure(
        u = f"""{asc} + od['time', 'b']""",
        scope = """True"""
    )
    choice_set = choice_model.get_choice_set()
    u_choices = choice_set.u_choices
    choice_labels = choice_set.choice_labels
    idx_car = [i for (i, (zone, trmode)) in enumerate(choice_labels) if trmode=='car']
    idx_bus = [i for (i, (zone, trmode)) in enumerate(choice_labels) if trmode=='bus']
    
    np.testing.assert_equal(
        u_choices[0, idx_car],
        choice_model.od['time', 'b', :, 'car']
    )
    np.testing.assert_equal(
        u_choices[0, idx_bus],
        10 + choice_model.od['time', 'b', :, 'bus']
    )


def test_get_probabilities(choice_model):
    choice_model.configure(
        u = f"""1 / od['time', 'b']""",
        scope = """True""",
        func_probabilities = lambda x: x
    )
    choices = choice_model.get_choice_set().u_choices
    probs = choice_model.get_selections().probabilities
    np.testing.assert_almost_equal(
        choices, probs
    )