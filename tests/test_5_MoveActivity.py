from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import modify

import pytest
import random
from datetime import datetime


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
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(16 * 60 + 30), end_time=mtdt(16 * 60 + 5)))
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 5), end_time=END_OF_DAY))
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


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_remove_individual_activities_when_given_person_and_activities(mocker, Smith_Household):
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'move_individual_activities')

    policy = modify.MoveActivityTourToHomeLocation([''])
    policy.apply_to(Smith_Household, Smith_Household['Bobby'], [Activity])

    modify.MoveActivityTourToHomeLocation.move_individual_activities.assert_called_once_with(Smith_Household['Bobby'], [Activity])


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_remove_person_activities_when_given_person(mocker, Smith_Household):
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'move_person_activities')

    policy = modify.MoveActivityTourToHomeLocation([''])
    policy.apply_to(Smith_Household, Smith_Household['Bobby'])

    modify.MoveActivityTourToHomeLocation.move_person_activities.assert_called_once_with(Smith_Household['Bobby'])


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_remove_household_activities_when_given_household(mocker, Smith_Household):
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'move_household_activities')

    policy = modify.MoveActivityTourToHomeLocation([''])
    policy.apply_to(Smith_Household)

    modify.MoveActivityTourToHomeLocation.move_household_activities.assert_called_once_with(Smith_Household)


def test_MoveActivityTourToHomeLocation_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = modify.MoveActivityTourToHomeLocation([''])
    with pytest.raises(NotImplementedError) as e:
        policy.apply_to(Bobby)
    assert 'Types passed incorrectly: <class \'pam.core.Person\'>, <class \'NoneType\'>, <class \'NoneType\'>. You need <class \'type\'> at the very least.' \
           in str(e.value)


def test_MoveActivityTourToHomeLocation_move_individual_activities_moves_an_activity_for_Bobby(Bobby):
    policy = modify.MoveActivityTourToHomeLocation(['education'])
    policy.move_individual_activities(Bobby, [Bobby.plan[2]])

    assert Bobby.plan[2].location == Bobby.home


def test_MoveActivityTourToHomeLocation_doesnt_move_individual_activities_for_Bobbys_empty_selected_activities_list(Bobby):
    policy = modify.MoveActivityTourToHomeLocation(['education'])
    policy.move_individual_activities(Bobby, [])

    assert Bobby.plan[2].location.loc == 'b'


def test_move_person_activities_delegates_to_remove_person_activities_for_Bobbys_activities(mocker, Bobby):
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'move_activities')

    policy = modify.MoveActivityTourToHomeLocation([''])
    policy.move_person_activities(Bobby)

    modify.MoveActivityTourToHomeLocation.move_activities.assert_called_once()


def test_move_household_activities_delegates_to_remove_person_activities_for_persons_in_household(mocker, Smith_Household):
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'move_person_activities')

    policy = modify.MoveActivityTourToHomeLocation([''])
    policy.move_household_activities(Smith_Household)

    assert modify.MoveActivityTourToHomeLocation.move_person_activities.call_count == 4


@pytest.fixture()
def activity_tours():
    return [[Activity(2, 'shop', 'a'), Activity(3, 'education', 'b')],
            [Activity(5, 'work', 'c'), Activity(6, 'shop', 'd')]]

@pytest.fixture()
def plain_filter():
    def filter(act):
        return True
    return filter


def test_matching_activity_tours_delegates_to_plan_activity_tours(mocker, plain_filter):
    mocker.patch.object(Plan, 'activity_tours')
    modify.MoveActivityTourToHomeLocation(['']).matching_activity_tours(Plan(1), plain_filter)

    Plan.activity_tours.assert_called_once()


def test_matching_activity_tours_delegates_to_tour_matches_activities(mocker, activity_tours, plain_filter):
    mocker.patch.object(Plan, 'activity_tours', return_value=[activity_tours[0]])
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'tour_matches_activities')
    modify.MoveActivityTourToHomeLocation(['']).matching_activity_tours(Plan(1), plain_filter)

    modify.MoveActivityTourToHomeLocation.tour_matches_activities.assert_called_once_with(activity_tours[0], plain_filter)


def test_matching_activity_tours_matches_one_tour(mocker, activity_tours, plain_filter):
    mocker.patch.object(Plan, 'activity_tours', return_value=activity_tours)
    mocker.patch.object(modify.MoveActivityTourToHomeLocation, 'tour_matches_activities', side_effect=[True, False])

    matching_tours = modify.MoveActivityTourToHomeLocation(['']).matching_activity_tours(Plan(1), plain_filter)

    assert matching_tours == [activity_tours[0]]


def test_tour_matches_activities_returns_True_when_there_is_a_matching_tour_and_plain_filter(activity_tours, plain_filter):
    assert modify.MoveActivityTourToHomeLocation(['education', 'shop']).tour_matches_activities(activity_tours[0], plain_filter)


def test_tour_matches_activities_returns_True_when_there_is_a_matching_tour_and_individual_filter(activity_tours):
    def is_a_selected_activity(act):
        for other_act in activity_tours[0]:
            if act.is_exact(other_act):
                return True
        return False
    assert modify.MoveActivityTourToHomeLocation(['education', 'shop']).tour_matches_activities(activity_tours[0], is_a_selected_activity)


def test_tour_matches_activities_returns_False_when_there_is_no_matching_tour_and_plain_filter(activity_tours, plain_filter):
    assert not modify.MoveActivityTourToHomeLocation(['education', 'shop']).tour_matches_activities(activity_tours[1], plain_filter)


def test_activity_is_part_of_tour(activity_tours):
    activity_in_tour = activity_tours[0][0]
    assert modify.MoveActivityTourToHomeLocation(['']).is_part_of_tour(activity_in_tour, activity_tours)


def test_activity_is_not_part_of_tour(activity_tours):
    activity_not_in_tour = Activity(0, 'blah', 'bleh')
    assert not modify.MoveActivityTourToHomeLocation(['']).is_part_of_tour(activity_not_in_tour, activity_tours)


def test_is_part_of_tour_delegates_to_is_exact_method(mocker):
    mocker.patch.object(Activity, 'is_exact')
    a = Activity(1)
    b = Activity(2)
    modify.MoveActivityTourToHomeLocation(['']).is_part_of_tour(a, [[b]])

    Activity.is_exact.assert_called_once_with(b)

