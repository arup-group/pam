from pam.policy import modifiers
from pam.policy import probability_samplers
from pam.policy import policies
from tests.fixtures import *


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan)-1].end_time == END_OF_DAY


def test_HouseholdPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, 'verify_probability')
    policies.HouseholdPolicy(modifiers.RemoveActivity(['']), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(0.5)


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'sample', return_value=True)

    policy = policies.HouseholdPolicy(modifiers.RemoveActivity(['']), probability_samplers.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    modifiers.RemoveActivity.apply_to.assert_called_once_with(household)


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'p', return_value=1)

    policy = policies.HouseholdPolicy(modifiers.RemoveActivity(['']), [1., probability_samplers.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    modifiers.RemoveActivity.apply_to.assert_called_once_with(household)


def test_PersonPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, 'verify_probability')
    policies.PersonPolicy(modifiers.RemoveActivity(['']), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(0.5, (probability_samplers.HouseholdProbability))


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'sample', return_value=True)

    policy = policies.PersonPolicy(modifiers.RemoveActivity(['']), probability_samplers.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'p', return_value=1)

    policy = policies.PersonPolicy(modifiers.RemoveActivity(['']), [1., probability_samplers.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(probability_samplers, 'verify_probability')
    policies.ActivityPolicy(modifiers.RemoveActivity(['']), 0.5)

    probability_samplers.verify_probability.assert_called_once_with(
        0.5, (probability_samplers.HouseholdProbability, probability_samplers.PersonProbability))


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'sample', return_value=True)

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(['']), probability_samplers.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, 'apply_to')
    mocker.patch.object(probability_samplers.SimpleProbability, 'p', return_value=1)

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(['']), [1., probability_samplers.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    assert modifiers.RemoveActivity.apply_to.call_count == 4

