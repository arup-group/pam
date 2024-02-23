import random
from copy import deepcopy

import numpy as np
import pytest
from pam.planner.choice_location import (
    ChoiceConfiguration,
    ChoiceMNL,
    ChoiceModel,
    DiscretionaryTripOD,
    DiscretionaryTrips,
)
from pam.planner.utils_planner import get_trip_chains_either_anchor, sample_weighted
from pytest import approx


@pytest.fixture
def population_planner_choice(population_no_args):
    for hid, pid, person in population_no_args.people():
        for act in person.activities:
            act.location.area = "a"
    return population_no_args


@pytest.fixture
def choice_model(population_planner_choice, od, data_zones) -> ChoiceModel:
    return ChoiceModel(population_planner_choice, od, data_zones)


@pytest.fixture
def choice_model_mnl(population_planner_choice, od, data_zones) -> ChoiceModel:
    return ChoiceMNL(population_planner_choice, od, data_zones)


@pytest.fixture
def discretionary_trip_od(plan_home_work_shop_home, od_discretionary):
    return DiscretionaryTripOD(
        trip_chain=get_trip_chains_either_anchor(plan_home_work_shop_home)[-1], od=od_discretionary
    )


@pytest.fixture
def discretionary_trip_od_multiple(plan_home_shop_shop_work_shop_shop_home, od_discretionary):
    return DiscretionaryTripOD(
        trip_chain=get_trip_chains_either_anchor(plan_home_shop_shop_work_shop_shop_home)[-1],
        od=od_discretionary,
    )


def test_zones_are_aligned(population_planner_choice, od, data_zones):
    choice_model = ChoiceModel(population_planner_choice, od, data_zones.loc[["b", "a"]])
    zones_destination = choice_model.od.labels.destination_zones
    zones_index = list(choice_model.zones.data.index)
    assert zones_destination == zones_index


@pytest.mark.parametrize("var", ["time", "distance"])
@pytest.mark.parametrize("zone", ["a", "b"])
def test_choice_set_reads_od_correctly(choice_model, var, zone):
    choice_model.configure(u=f"""1 / od['{var}', '{zone}']""", scope="""act.act=='work'""")
    choice_set = choice_model.get_choice_set()
    assert choice_set.choice_labels == [("a", "car"), ("a", "bus"), ("b", "car"), ("b", "bus")]
    for choice in choice_set.u_choices:
        np.testing.assert_array_equal(choice, 1 / choice_model.od[var, zone].flatten())


def test_list_parameters_correspond_to_modes(choice_model):
    """When utility parameters are passed as a list,
    they should be applied to each respective mode.
    """
    asc = [0, 10]  # 0 should be applied to car, 10 to bus
    choice_model.configure(u=f"""{asc} + od['time', 'b']""", scope="""True""")
    choice_set = choice_model.get_choice_set()
    u_choices = choice_set.u_choices
    choice_labels = choice_set.choice_labels
    idx_car = [i for (i, (zone, trmode)) in enumerate(choice_labels) if trmode == "car"]
    idx_bus = [i for (i, (zone, trmode)) in enumerate(choice_labels) if trmode == "bus"]

    np.testing.assert_equal(u_choices[0, idx_car], choice_model.od["time", "b", :, "car"])
    np.testing.assert_equal(u_choices[0, idx_bus], 10 + choice_model.od["time", "b", :, "bus"])


def test_get_probabilities_along_dimension(choice_model):
    choice_model.configure(
        u="""1 / od['time', 'b']""",
        scope="""True""",
        func_probabilities=lambda x: x / sum(x),
        func_sampling=sample_weighted,
    )
    choices = choice_model.get_choice_set().u_choices
    probs = choice_model.selections.probabilities
    assert (probs.sum(axis=1) == 1).all()
    np.testing.assert_almost_equal(choices / choices.sum(1).reshape(-1, 1), probs)


def test_apply_once_per_agent_same_locations(choice_model_mnl):
    choice_model_mnl.configure(
        u="""1 / od['time', 'b']""", scope="""True""", func_probabilities=lambda x: x / sum(x)
    )

    def assert_single_location(population_planner_choice):
        for hid, pid, person in population_planner_choice.people():
            locs = [act.location.area for act in person.plan.activities]
            assert len(set(locs)) == 1

    with pytest.raises(AssertionError):
        random.seed(10)
        choice_model_mnl.apply(once_per_agent=False)
        assert_single_location(choice_model_mnl.population)

    # only apply once per agent:
    choice_model_mnl.apply(once_per_agent=True)
    # now all locations should be in the same zone
    # for each agent
    assert_single_location(choice_model_mnl.population)


def test_nonset_config_attribute_valitation_raise_error():
    config = ChoiceConfiguration()

    with pytest.raises(ValueError):
        config.validate(["u", "scope"])

    config.u = "1"
    config.scope = "True"
    config.validate(["u", "scope"])


def test_model_checks_config_requirements(mocker, choice_model_mnl):
    mocker.patch.object(ChoiceConfiguration, "validate")
    choice_model_mnl.configure(u="""1 / od['time', 'a']""", scope="""act.act=='work'""")

    choice_model_mnl.get_choice_set()
    ChoiceConfiguration.validate.assert_called_once_with(["u", "scope"])


def test_utility_calculation(choice_model_mnl):
    scope = "act.act=='work'"
    asc = [0, -1]
    asc_shift_poor = [0, 2]
    beta_time = [-0.05, -0.07]
    beta_zones = 0.4
    utility_calc = f""" \
        {asc} + \
        (np.array({asc_shift_poor}) * (person.attributes['subpopulation']=='poor')) + \
        ({beta_time} * od['time', person.home.area]) + \
        ({beta_zones} * np.log(zones.jobs))
    """
    choice_model_mnl.configure(u=utility_calc, scope=scope)

    np.testing.assert_almost_equal(
        np.array(
            [0.8420680743952365, -1.2579319256047636, 0.11932694661921461, -2.0306730533807857]
        ),
        choice_model_mnl.get_choice_set().u_choices[0],
    )


def test_match_leg_ratio_probabilities(discretionary_trip_od: DiscretionaryTripOD):
    assert approx(discretionary_trip_od.leg_ratios, abs=0.005) == [0.667, 0.500, 0.333]
    assert approx(discretionary_trip_od.leg_ratio_p, abs=0.005) == [0.444, 0.667, 0.889]


def test_match_diversion_probabilities(discretionary_trip_od: DiscretionaryTripOD):
    assert approx(discretionary_trip_od.diversion_p, abs=0.005) == [0.545, 0.545, 0.545]


def test_match_attraction_probabilities(discretionary_trip_od: DiscretionaryTripOD):
    assert approx(discretionary_trip_od.attraction_p, abs=0.005) == [0.231, 0.306, 0.463]


def test_match_destination_probabilities(discretionary_trip_od: DiscretionaryTripOD):
    assert approx(discretionary_trip_od.destination_p, abs=0.00000005) == [
        0.14289797,
        0.28551015,
        0.57159188,
    ]


def test_all_discretionary_locations_updated(
    plan_home_shop_shop_work_shop_shop_home, od_discretionary
):
    plan_prior = deepcopy(plan_home_shop_shop_work_shop_shop_home)

    DiscretionaryTrips(
        plan=plan_home_shop_shop_work_shop_shop_home, od=od_discretionary
    ).update_plan()

    activities_prior = list(plan_prior.activities)
    activities_post = list(plan_home_shop_shop_work_shop_shop_home.activities)

    # anchor positions have not changed
    for i in [0, 3, 6]:
        assert activities_prior[i].location.area == activities_post[i].location.area

    # all discretionary locations should have changed
    for i in [1, 2, 4, 5]:
        assert activities_prior[i].location.area != activities_post[i].location.area
