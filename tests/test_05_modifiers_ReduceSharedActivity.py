import random

import pytest
from pam.activity import Activity, Leg
from pam.core import Person
from pam.policy import modifiers
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


@pytest.fixture()
def Bobber():
    Bobber = Person(
        "Bobber", attributes={"age": 6, "job": "education", "gender": "male", "key_worker": False}
    )
    Bobber.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobber.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobber.add(Activity(2, "education", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobber.add(Leg(2, "walk", "b", "c", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobber.add(Activity(3, "home", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(18 * 60)))
    Bobber.add(Leg(3, "car", "a", "b", start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Bobber.add(
        Activity(4, "shop_1", "b", start_time=mtdt(18 * 60 + 20), end_time=mtdt(18 * 60 + 50))
    )
    Bobber.add(Leg(4, "walk", "b", "b", start_time=mtdt(18 * 60 + 50), end_time=mtdt(19 * 60)))
    Bobber.add(Activity(5, "shop_2", "b", start_time=mtdt(19 * 60), end_time=mtdt(19 * 60 + 50)))
    Bobber.add(Leg(5, "car", "b", "a", start_time=mtdt(19 * 60 + 50), end_time=mtdt(20 * 60 + 10)))
    Bobber.add(Activity(6, "home", "a", start_time=mtdt(20 * 60 + 10), end_time=END_OF_DAY))
    return Bobber


@pytest.fixture()
def Betty():
    Betty = Person(
        "Betty", attributes={"age": 40, "job": "work", "gender": "female", "key_worker": True}
    )
    Betty.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Betty.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Betty.add(Activity(2, "escort", "b", start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)))
    Betty.add(Leg(2, "pt", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Betty.add(Activity(3, "work", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Betty.add(Leg(3, "pt", "b", "c", start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Betty.add(
        Activity(4, "leisure", "c", start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20))
    )
    Betty.add(Leg(4, "pt", "c", "b", start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Betty.add(Activity(5, "escort", "b", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Betty.add(Leg(5, "walk", "a", "b", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Betty.add(Activity(6, "home", "a", start_time=mtdt(17 * 60), end_time=mtdt(18 * 60)))
    Betty.add(Leg(6, "car", "a", "b", start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Betty.add(
        Activity(7, "shop_1", "b", start_time=mtdt(18 * 60 + 20), end_time=mtdt(18 * 60 + 50))
    )
    Betty.add(Leg(7, "walk", "b", "b", start_time=mtdt(18 * 60 + 50), end_time=mtdt(19 * 60)))
    Betty.add(Activity(8, "shop_2", "b", start_time=mtdt(19 * 60), end_time=mtdt(19 * 60 + 50)))
    Betty.add(Leg(8, "car", "b", "a", start_time=mtdt(19 * 60 + 50), end_time=mtdt(20 * 60 + 10)))
    Betty.add(Activity(9, "home", "a", start_time=mtdt(20 * 60 + 10), end_time=END_OF_DAY))
    return Betty


def test_remove_activities_removes_single_activity(assert_correct_activities, Betty):
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )
    modifiers.ReduceSharedActivity(["shop_1"]).remove_activities(
        Betty, shared_activities_for_removal=[Betty.plan[12]]
    )
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_2",
            "home",
        ],
    )


def test_remove_activities_removes_adjoining_activities(assert_correct_activities, Betty):
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )
    modifiers.ReduceSharedActivity(["shop_1", "shop_2"]).remove_activities(
        Betty, shared_activities_for_removal=[Betty.plan[12], Betty.plan[14]]
    )
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=["home", "escort", "work", "leisure", "escort", "home"],
    )


@pytest.mark.xfail()  # fails because of the bug
def test_remove_activities_removes_relevant_shared_activities(assert_correct_activities, Betty):
    Betty.plan[6].act = "shop_1"
    Betty.plan[6].location = Betty.plan[12].location
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "shop_1",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )
    modifiers.ReduceSharedActivity(["shop_1", "shop_2"]).remove_activities(
        Betty, shared_activities_for_removal=[Betty.plan[12], Betty.plan[14]]
    )
    assert_correct_activities(
        person=Betty, ordered_activities_list=["home", "escort", "work", "shop_1", "escort", "home"]
    )


def test_remove_household_activities_does_nothing_if_people_in_hhld_dont_share_acts(
    assert_correct_activities, SmithHousehold
):
    household = SmithHousehold
    steve = household.people[1]
    hilda = household.people[2]
    timmy = household.people[3]
    bobby = household.people[4]
    assert_correct_activities(
        person=steve, ordered_activities_list=["home", "work", "leisure", "work", "home"]
    )
    assert_correct_activities(
        person=hilda,
        ordered_activities_list=[
            "home",
            "escort_education",
            "shop",
            "leisure",
            "escort_education",
            "home",
        ],
    )
    assert_correct_activities(
        person=timmy,
        ordered_activities_list=["home", "education", "shop", "education", "leisure", "home"],
    )
    assert_correct_activities(person=bobby, ordered_activities_list=["home", "education", "home"])

    policy = modifiers.ReduceSharedActivity([""])
    shared_acts = policy.shared_activities_for_removal(household)
    assert not shared_acts

    policy.remove_household_activities(household)
    assert_correct_activities(
        person=steve, ordered_activities_list=["home", "work", "leisure", "work", "home"]
    )
    assert_correct_activities(
        person=hilda,
        ordered_activities_list=[
            "home",
            "escort_education",
            "shop",
            "leisure",
            "escort_education",
            "home",
        ],
    )
    assert_correct_activities(
        person=timmy,
        ordered_activities_list=["home", "education", "shop", "education", "leisure", "home"],
    )
    assert_correct_activities(person=bobby, ordered_activities_list=["home", "education", "home"])


def test_remove_household_activities_does_nothing_if_one_person_in_hhld(
    assert_correct_activities, instantiate_household_with, Betty
):
    household = instantiate_household_with([Betty])
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )

    policy = modifiers.ReduceSharedActivity([""])
    shared_acts = policy.shared_activities_for_removal(household)
    assert not shared_acts

    policy.remove_household_activities(household)
    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )


def test_remove_household_activities_removes_Bettys_shopping_shared_activities(
    instantiate_household_with, assert_correct_activities, mocker, Betty, Bobber
):
    mocker.patch.object(random, "choice", return_value=Betty)
    hhld = instantiate_household_with([Betty, Bobber])
    policy = modifiers.ReduceSharedActivity(["shop_1", "shop_2"])

    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )
    assert_correct_activities(
        person=Bobber,
        ordered_activities_list=["home", "education", "home", "shop_1", "shop_2", "home"],
    )

    policy.remove_household_activities(hhld)

    assert_correct_activities(
        person=Betty,
        ordered_activities_list=[
            "home",
            "escort",
            "work",
            "leisure",
            "escort",
            "home",
            "shop_1",
            "shop_2",
            "home",
        ],
    )
    assert_correct_activities(person=Bobber, ordered_activities_list=["home", "education", "home"])


def test_shared_activities_for_removal_finds_shared_activities(
    instantiate_household_with, Betty, Bobber
):
    hhld = instantiate_household_with([Betty, Bobber])
    act_1 = Activity(8, "shop_2", "b", start_time=mtdt(19 * 60), end_time=mtdt(19 * 60 + 50))
    act_2 = Activity(7, "shop_1", "b", start_time=mtdt(18 * 60 + 20), end_time=mtdt(18 * 60 + 50))

    shared_acts = modifiers.ReduceSharedActivity(
        ["shop_1", "shop_2"]
    ).shared_activities_for_removal(hhld)

    assert shared_acts
    assert act_1.isin_exact(shared_acts)
    assert act_2.isin_exact(shared_acts)


def test_people_who_share_activities_for_removal_identifies_both_people_as_sharing_activities(
    instantiate_household_with, Betty, Bobber
):
    hhld = instantiate_household_with([Betty, Bobber])

    ppl = modifiers.ReduceSharedActivity(
        ["shop_1", "shop_2"]
    ).people_who_share_activities_for_removal(hhld)

    assert ppl
    assert Betty in ppl
    assert Bobber in ppl


def test_apply_to_delegates_to_remove_activities_when_given_household(mocker, SmithHousehold):
    mocker.patch.object(modifiers.ReduceSharedActivity, "remove_household_activities")

    policy = modifiers.ReduceSharedActivity([""])
    policy.apply_to(SmithHousehold)

    modifiers.ReduceSharedActivity.remove_household_activities.assert_called_once_with(
        SmithHousehold
    )


def test_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = modifiers.ReduceSharedActivity([""])
    with pytest.raises(NotImplementedError) as e:
        policy.apply_to(Bobby)
    assert (
        "Types passed incorrectly: <class 'pam.core.Person'>, <class 'NoneType'>, <class 'NoneType'>. "
        "This modifier exists only for Households" in str(e.value)
    )


def test_remove_household_activities_delegates_to_several_methods(mocker, SmithHousehold):
    mocker.patch.object(
        modifiers.ReduceSharedActivity, "shared_activities_for_removal", return_value=[""]
    )
    mocker.patch.object(
        modifiers.ReduceSharedActivity, "people_who_share_activities_for_removal", return_value=[""]
    )
    mocker.patch.object(random, "choice")
    mocker.patch.object(modifiers.ReduceSharedActivity, "remove_activities")

    policy = modifiers.ReduceSharedActivity([""])
    policy.remove_household_activities(SmithHousehold)

    modifiers.ReduceSharedActivity.shared_activities_for_removal.assert_called_once_with(
        SmithHousehold
    )
    assert modifiers.ReduceSharedActivity.people_who_share_activities_for_removal.call_count == 2
    random.choice.assert_called_once_with([""])
    assert modifiers.ReduceSharedActivity.remove_activities.call_count == 4


def test_is_activity_for_removal_activity_matches_ReduceSharedActivity_activities():
    activity = Activity(act="some_activity")
    policy_remove_activity = modifiers.ReduceSharedActivity(["some_activity"])

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_ReduceSharedActivity_activities():
    activity = Activity(act="other_activity")
    policy_remove_activity = modifiers.ReduceSharedActivity(["some_activity"])

    assert not policy_remove_activity.is_activity_for_removal(activity)
