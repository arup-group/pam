import random

import pytest
from pam.activity import Activity
from pam.policy import filters, modifiers, policies, probability_samplers
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan) - 1].end_time == END_OF_DAY


@pytest.fixture()
def dummy_filter():
    class MyFilter(filters.Filter):
        def __init__(self):
            super().__init__()

        def satisfies_conditions(self, x):
            super().satisfies_conditions(x)

    return MyFilter()


def test_HouseholdPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, "verify_probability")
    policies.HouseholdPolicy(modifiers.RemoveActivity([""]), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(0.5)


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(probability_samplers.SimpleProbability, "sample", return_value=True)

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity([""]), probability_samplers.SimpleProbability(1.0)
    )
    household = SmithHousehold

    policy.apply_to(household)

    modifiers.RemoveActivity.apply_to.assert_called_once_with(household)


def test_HouseholdPolicy_does_nothing_if_attribute_filter_condition_not_satisfied(
    mocker, SmithHousehold, dummy_filter
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(filters.Filter, "satisfies_conditions", return_value=False)

    policy = policies.HouseholdPolicy(modifiers.RemoveActivity([""]), 0.5, dummy_filter)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_HouseholdPolicy_does_nothing_if_not_selected_for_single_probability(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.7)

    policy = policies.HouseholdPolicy(modifiers.RemoveActivity([""]), 0.5)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity([""]), [1.0, probability_samplers.SimpleProbability(1.0)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    modifiers.RemoveActivity.apply_to.assert_called_once_with(household)


def test_HouseholdPolicy_does_nothing_if_not_selected_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.5)

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity([""]), [0.5, probability_samplers.SimpleProbability(0.5)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_PersonPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, "verify_probability")
    policies.PersonPolicy(modifiers.RemoveActivity([""]), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(
        0.5, (probability_samplers.HouseholdProbability)
    )


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(probability_samplers.SimpleProbability, "sample", return_value=True)

    policy = policies.PersonPolicy(
        modifiers.RemoveActivity([""]), probability_samplers.SimpleProbability(1.0)
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_PersonPolicy_does_nothing_if_attribute_filter_condition_not_satisfied(
    mocker, SmithHousehold, dummy_filter
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(filters.Filter, "satisfies_conditions", return_value=False)

    policy = policies.PersonPolicy(modifiers.RemoveActivity([""]), 0.5, dummy_filter)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_PersonPolicy_does_nothing_if_not_selected_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.7)

    policy = policies.PersonPolicy(modifiers.RemoveActivity([""]), 0.5)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(probability_samplers.SimpleProbability, "p", return_value=1)

    policy = policies.PersonPolicy(
        modifiers.RemoveActivity([""]), [1.0, probability_samplers.SimpleProbability(1.0)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_PersonPolicy_does_nothing_if_not_selected_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.5)

    policy = policies.PersonPolicy(
        modifiers.RemoveActivity([""]), [0.5, probability_samplers.SimpleProbability(0.5)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_ActivityPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, "verify_probability")
    policies.ActivityPolicy(modifiers.RemoveActivity([""]), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(
        0.5, (probability_samplers.HouseholdProbability, probability_samplers.PersonProbability)
    )


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(probability_samplers.SimpleProbability, "sample", return_value=True)

    policy = policies.ActivityPolicy(
        modifiers.RemoveActivity([""]), probability_samplers.SimpleProbability(1.0)
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_does_nothing_if_attribute_filter_condition_not_satisfied(
    mocker, SmithHousehold, dummy_filter
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(filters.Filter, "satisfies_conditions", return_value=False)

    policy = policies.ActivityPolicy(modifiers.RemoveActivity([""]), 0.5, dummy_filter)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_ActivityPolicy_does_nothing_if_not_selected_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.7)

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(["work"]), 0.5)
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(probability_samplers.SimpleProbability, "p", return_value=1)

    policy = policies.ActivityPolicy(
        modifiers.RemoveActivity([""]), [1.0, probability_samplers.SimpleProbability(1.0)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_does_nothing_if_not_selected_for_list_of_probabilities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "apply_to")
    mocker.patch.object(random, "random", return_value=0.7)

    policy = policies.ActivityPolicy(
        modifiers.RemoveActivity([""]), [0.5, probability_samplers.SimpleProbability(0.5)]
    )
    household = SmithHousehold

    policy.apply_to(household)

    assert not modifiers.RemoveActivity.apply_to.called, "method should not have been called"
