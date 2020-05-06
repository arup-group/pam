from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import modify
import pytest
from tests.fixtures import *


def test_RemoveActivity_apply_to_delegates_to_remove_individual_activities_when_given_person_and_activities(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'remove_individual_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(SmithHousehold, SmithHousehold['4'], [Activity])

    modify.RemoveActivity.remove_individual_activities.assert_called_once_with(SmithHousehold['4'], [Activity])


def test_RemoveActivity_apply_to_delegates_to_remove_person_activities_when_given_person(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(SmithHousehold, SmithHousehold['4'])

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(SmithHousehold['4'])


def test_RemoveActivity_apply_to_delegates_to_remove_household_activities_when_given_household(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(SmithHousehold)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(SmithHousehold)


def test_RemoveActivity_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = modify.RemoveActivity([''])
    with pytest.raises(NotImplementedError) as e:
        policy.apply_to(Bobby)
    assert 'Types passed incorrectly: <class \'pam.core.Person\'>, <class \'NoneType\'>, <class \'NoneType\'>. You need <class \'type\'> at the very least.' \
           in str(e.value)


def test_remove_activities_removes_Bobbys_education(Bobby):
    policy = modify.RemoveActivity(['education'])
    def fnc(act): return True
    policy.remove_activities(Bobby, fnc)

    assert_correct_activities(Bobby, ['home'])


def test_remove_individual_activities_delegates_to_remove_activities_for_Bobby(mocker, Bobby):
    mocker.patch.object(modify.RemoveActivity, 'remove_activities')

    policy = modify.RemoveActivity([''])
    policy.remove_individual_activities(Bobby, [''])

    modify.RemoveActivity.remove_activities.assert_called_once()


def test_remove_person_activities_delegates_to_remove_activities_for_Bobbys_activities(mocker, Bobby):
    mocker.patch.object(modify.RemoveActivity, 'remove_activities')

    policy = modify.RemoveActivity([''])
    policy.remove_person_activities(Bobby)

    modify.RemoveActivity.remove_activities.assert_called_once()


def test_remove_household_activities_delegates_to_remove_person_activities_for_persons_in_household(mocker, SmithHousehold):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')

    policy = modify.RemoveActivity([''])
    policy.remove_household_activities(SmithHousehold)

    assert modify.RemoveActivity.remove_person_activities.call_count == 4


def test_is_activity_for_removal_activity_matches_RemoveActivity_activities():
    activity = Activity(act = 'some_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'])

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_RemoveActivity_activities():
    activity = Activity(act = 'other_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'])

    assert not policy_remove_activity.is_activity_for_removal(activity)