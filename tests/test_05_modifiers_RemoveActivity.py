import pytest
from pam.activity import Activity
from pam.policy import modifiers


def test_RemoveActivity_apply_to_delegates_to_remove_individual_activities_when_given_person_and_activities(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_individual_activities")

    policy = modifiers.RemoveActivity([""])
    policy.apply_to(SmithHousehold, SmithHousehold[4], [Activity])

    modifiers.RemoveActivity.remove_individual_activities.assert_called_once_with(
        SmithHousehold[4], [Activity]
    )


def test_RemoveActivity_apply_to_delegates_to_remove_person_activities_when_given_person(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")

    policy = modifiers.RemoveActivity([""])
    policy.apply_to(SmithHousehold, SmithHousehold[4])

    modifiers.RemoveActivity.remove_person_activities.assert_called_once_with(SmithHousehold[4])


def test_RemoveActivity_apply_to_delegates_to_remove_household_activities_when_given_household(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")

    policy = modifiers.RemoveActivity([""])
    policy.apply_to(SmithHousehold)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(SmithHousehold)


def test_RemoveActivity_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = modifiers.RemoveActivity([""])
    with pytest.raises(TypeError) as e:
        policy.apply_to(Bobby)
    assert (
        "Types passed incorrectly: <class 'pam.core.Person'>, <class 'NoneType'>, <class 'NoneType'>. You need <class 'type'> at the very least."
        in str(e.value)
    )


def test_remove_activities_removes_Bobbys_education(assert_correct_activities, Bobby):
    policy = modifiers.RemoveActivity(["education"])

    def fnc(act):
        return True

    policy.remove_activities(Bobby, fnc)

    assert_correct_activities(Bobby, ["home"])


def test_remove_individual_activities_delegates_to_remove_activities_for_Bobby(mocker, Bobby):
    mocker.patch.object(modifiers.RemoveActivity, "remove_activities")

    policy = modifiers.RemoveActivity([""])
    policy.remove_individual_activities(Bobby, [""])

    modifiers.RemoveActivity.remove_activities.assert_called_once()


def test_remove_person_activities_delegates_to_remove_activities_for_Bobbys_activities(
    mocker, Bobby
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_activities")

    policy = modifiers.RemoveActivity([""])
    policy.remove_person_activities(Bobby)

    modifiers.RemoveActivity.remove_activities.assert_called_once()


def test_remove_household_activities_delegates_to_remove_person_activities_for_persons_in_household(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")

    policy = modifiers.RemoveActivity([""])
    policy.remove_household_activities(SmithHousehold)

    assert modifiers.RemoveActivity.remove_person_activities.call_count == 4


def test_is_activity_for_removal_activity_matches_RemoveActivity_activities():
    activity = Activity(act="some_activity")
    policy_remove_activity = modifiers.RemoveActivity(["some_activity"])

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_RemoveActivity_activities():
    activity = Activity(act="other_activity")
    policy_remove_activity = modifiers.RemoveActivity(["some_activity"])

    assert not policy_remove_activity.is_activity_for_removal(activity)
