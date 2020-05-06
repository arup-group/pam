from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import modify
import pytest


def instantiate_household_with(persons: list):
    household = Household(1)
    for person in persons:
        household.add(person)
    return household


@pytest.fixture()
def Steve():
    Steve = Person('Steve', attributes={'age': 50, 'job': 'work', 'gender': 'male'})
    Steve.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(5 * 60)))
    Steve.add(Leg(1, 'car', 'a', 'b', start_time=mtdt(5 * 60), end_time=mtdt(6 * 60)))
    Steve.add(Activity(2, 'work', 'b', start_time=mtdt(6 * 60), end_time=mtdt(12 * 60)))
    Steve.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 10)))
    Steve.add(Activity(3, 'leisure', 'c', start_time=mtdt(12 * 60 + 10), end_time=mtdt(13 * 60 - 10)))
    Steve.add(Leg(3, 'walk', 'c', 'b', start_time=mtdt(13 * 60 - 10), end_time=mtdt(13 * 60)))
    Steve.add(Activity(4, 'work', 'b', start_time=mtdt(13 * 60), end_time=mtdt(18 * 60)))
    Steve.add(Leg(4, 'car', 'b', 'a', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)))
    Steve.add(Activity(5, 'home', 'a', start_time=mtdt(19 * 60), end_time=END_OF_DAY))
    return Steve


@pytest.fixture()
def Hilda():
    Hilda = Person('Hilda', attributes={'age': 45, 'job': 'influencer', 'gender': 'female'})
    Hilda.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Leg(1, 'pt', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, 'shop', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Hilda.add(Leg(2, 'pt', 'b', 'c', start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Hilda.add(Activity(3, 'leisure', 'c', start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20)))
    Hilda.add(Leg(3, 'pt', 'c', 'b', start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    return Hilda


@pytest.fixture()
def Timmy():
    Timmy = Person('Timmy', attributes={'age': 18, 'job': 'education', 'gender': 'male'})
    Timmy.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(10 * 60)))
    Timmy.add(Leg(1, 'bike', 'a', 'b', start_time=mtdt(10 * 60), end_time=mtdt(11 * 60)))
    Timmy.add(Activity(2, 'education', 'b', start_time=mtdt(11 * 60), end_time=mtdt(13 * 60)))
    Timmy.add(Leg(2, 'bike', 'b', 'c', start_time=mtdt(13 * 60), end_time=mtdt(13 * 60 + 5)))
    Timmy.add(Activity(3, 'shop', 'c', start_time=mtdt(13 * 60 + 5), end_time=mtdt(13 * 60 + 30)))
    Timmy.add(Leg(3, 'bike', 'c', 'b', start_time=mtdt(13 * 60 + 30), end_time=mtdt(13 * 60 + 35)))
    Timmy.add(Activity(4, 'education', 'b', start_time=mtdt(13 * 60 + 35), end_time=mtdt(15 * 60)))
    Timmy.add(Leg(4, 'bike', 'b', 'd', start_time=mtdt(15 * 60), end_time=mtdt(15 * 60 + 10)))
    Timmy.add(Activity(5, 'leisure', 'd', start_time=mtdt(15 * 60 + 10), end_time=mtdt(18 * 60)))
    Timmy.add(Leg(5, 'bike', 'd', 'a', start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Timmy.add(Activity(6, 'home', 'a', start_time=mtdt(18 * 60 + 20), end_time=END_OF_DAY))
    return Timmy


@pytest.fixture()
def Bobby():
    Bobby = Person('Bobby', attributes={'age': 6, 'job': 'education', 'gender': 'non-binary'})
    Bobby.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobby.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobby.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobby.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobby.add(Activity(5, 'home', 'a', start_time=mtdt(18 * 60 + 30), end_time=END_OF_DAY))
    return Bobby


@pytest.fixture()
def Smith_Household(Steve, Hilda, Timmy, Bobby):
    return instantiate_household_with([Steve, Hilda, Timmy, Bobby])


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan)-1].end_time == END_OF_DAY


def test_RemoveActivity_apply_to_delegates_to_remove_individual_activities_when_given_person_and_activities(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_individual_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(Smith_Household, Smith_Household['Bobby'], [Activity])

    modify.RemoveActivity.remove_individual_activities.assert_called_once_with(Smith_Household['Bobby'], [Activity])


def test_RemoveActivity_apply_to_delegates_to_remove_person_activities_when_given_person(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(Smith_Household, Smith_Household['Bobby'])

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(Smith_Household['Bobby'])


def test_RemoveActivity_apply_to_delegates_to_remove_household_activities_when_given_household(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')

    policy = modify.RemoveActivity([''])
    policy.apply_to(Smith_Household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(Smith_Household)


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


def test_remove_household_activities_delegates_to_remove_person_activities_for_persons_in_household(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')

    policy = modify.RemoveActivity([''])
    policy.remove_household_activities(Smith_Household)

    assert modify.RemoveActivity.remove_person_activities.call_count == 4


def test_is_activity_for_removal_activity_matches_RemoveActivity_activities():
    activity = Activity(act = 'some_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'])

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_RemoveActivity_activities():
    activity = Activity(act = 'other_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'])

    assert not policy_remove_activity.is_activity_for_removal(activity)