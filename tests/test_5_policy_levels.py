from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import modify
import builtins
from tests.fixtures import *
import pytest
import random
from datetime import datetime


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan)-1].end_time == END_OF_DAY


def test_HouseholdPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(modify, 'verify_probability')
    modify.HouseholdPolicy(modify.RemoveActivity(['']), 0.5)

    modify.verify_probability.assert_called_once_with(
        0.5,
        (float, list, modify.SimpleProbability, modify.ActivityProbability, modify.PersonProbability,
         modify.HouseholdProbability)
    )


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'sample', return_value=True)

    policy = modify.HouseholdPolicy(modify.RemoveActivity(['']), modify.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    modify.RemoveActivity.apply_to.assert_called_once_with(household)


def test_HouseholdPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'p', return_value=1)

    policy = modify.HouseholdPolicy(modify.RemoveActivity(['']), [1., modify.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    modify.RemoveActivity.apply_to.assert_called_once_with(household)


def test_PersonPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(modify, 'verify_probability')
    modify.PersonPolicy(modify.RemoveActivity(['']), 0.5)

    modify.verify_probability.assert_called_once_with(
        0.5,
        (float, list, modify.SimpleProbability, modify.ActivityProbability, modify.PersonProbability)
    )


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'sample', return_value=True)

    policy = modify.PersonPolicy(modify.RemoveActivity(['']), modify.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    assert modify.RemoveActivity.apply_to.call_count == 4


def test_PersonPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'p', return_value=1)

    policy = modify.PersonPolicy(modify.RemoveActivity(['']), [1., modify.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    assert modify.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_verifies_for_appropriate_probabilities(mocker):
    mocker.patch.object(modify, 'verify_probability')
    modify.ActivityPolicy(modify.RemoveActivity(['']), 0.5)

    modify.verify_probability.assert_called_once_with(
        0.5,
        (float, list, modify.SimpleProbability, modify.ActivityProbability)
    )


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_single_probability(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'sample', return_value=True)

    policy = modify.ActivityPolicy(modify.RemoveActivity(['']), modify.SimpleProbability(1.))
    household = SmithHousehold

    policy.apply_to(household)

    assert modify.RemoveActivity.apply_to.call_count == 4


def test_ActivityPolicy_apply_to_delegates_to_modifier_policy_apply_to_for_list_of_probabilities(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'apply_to')
    mocker.patch.object(modify.SimpleProbability, 'p', return_value=1)

    policy = modify.ActivityPolicy(modify.RemoveActivity(['']), [1., modify.SimpleProbability(1.)])
    household = SmithHousehold

    policy.apply_to(household)

    assert modify.RemoveActivity.apply_to.call_count == 4

