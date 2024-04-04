import pytest
from pam.activity import Activity, Plan
from pam.policy.modifiers import MoveActivityTourToHomeLocation
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan) - 1].end_time == END_OF_DAY


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_helper_when_given_person_and_activities(
    mocker, SmithHousehold
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_individual_activities")

    policy = MoveActivityTourToHomeLocation([""], new_mode="car")
    policy.apply_to(SmithHousehold, SmithHousehold[4], [Activity])

    MoveActivityTourToHomeLocation.move_individual_activities.assert_called_once_with(
        SmithHousehold[4], [Activity], "car"
    )


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_helper_when_given_person_and_activities_default_new_mode(
    mocker, SmithHousehold
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_individual_activities")

    policy = MoveActivityTourToHomeLocation([""])
    policy.apply_to(SmithHousehold, SmithHousehold[4], [Activity])

    MoveActivityTourToHomeLocation.move_individual_activities.assert_called_once_with(
        SmithHousehold[4], [Activity], "walk"
    )


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_helper_when_given_given_person(
    mocker, SmithHousehold
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_person_activities")

    policy = MoveActivityTourToHomeLocation([""])
    policy.apply_to(SmithHousehold, SmithHousehold[4])

    MoveActivityTourToHomeLocation.move_person_activities.assert_called_once_with(
        SmithHousehold[4], "walk"
    )


def test_MoveActivityTourToHomeLocation_apply_to_delegates_to_helper_when_given_household(
    mocker, SmithHousehold
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_household_activities")

    policy = MoveActivityTourToHomeLocation([""])
    policy.apply_to(SmithHousehold)

    MoveActivityTourToHomeLocation.move_household_activities.assert_called_once_with(
        SmithHousehold, "walk"
    )


def test_MoveActivityTourToHomeLocation_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = MoveActivityTourToHomeLocation([""])
    with pytest.raises(NotImplementedError) as e:
        policy.apply_to(Bobby)
    assert (
        "Types passed incorrectly: <class 'pam.core.Person'>, <class 'NoneType'>, <class 'NoneType'>. You need <class 'type'> at the very least."
        in str(e.value)
    )


def test_MoveActivityTourToHomeLocation_move_individual_activities_moves_an_activity(Bobby):
    policy = MoveActivityTourToHomeLocation(["education"])
    policy.move_individual_activities(Bobby, [Bobby.plan[2]])

    assert Bobby.plan[2].location == Bobby.home


def test_MoveActivityTourToHomeLocation_doesnt_move_individual_activities_empty_selected_activities_list(
    Bobby,
):
    policy = MoveActivityTourToHomeLocation(["education"])
    policy.move_individual_activities(Bobby, [])

    assert Bobby.plan[2].location.area == "b"


def test_move_person_activities_delegates_to_remove_person_activities_for_persons_activities(
    mocker, Bobby
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_activities")

    policy = MoveActivityTourToHomeLocation([""])
    policy.move_person_activities(Bobby)

    MoveActivityTourToHomeLocation.move_activities.assert_called_once()


def test_move_household_activities_delegates_to_remove_person_activities_for_persons_in_household(
    mocker, SmithHousehold
):
    mocker.patch.object(MoveActivityTourToHomeLocation, "move_person_activities")

    policy = MoveActivityTourToHomeLocation([""])
    policy.move_household_activities(SmithHousehold)

    assert MoveActivityTourToHomeLocation.move_person_activities.call_count == 4


@pytest.fixture()
def activity_tours():
    return [
        [Activity(2, "shop", "a"), Activity(3, "education", "b")],
        [Activity(5, "work", "c"), Activity(6, "shop", "d")],
    ]


@pytest.fixture()
def plain_filter():
    def filter(act):
        return True

    return filter


def test_matching_activity_tours_delegates_to_plan_activity_tours(mocker, plain_filter):
    mocker.patch.object(Plan, "activity_tours")
    MoveActivityTourToHomeLocation([""]).matching_activity_tours(Plan(1), plain_filter)

    Plan.activity_tours.assert_called_once()


def test_matching_activity_tours_delegates_to_tour_matches_activities(
    mocker, activity_tours, plain_filter
):
    mocker.patch.object(Plan, "activity_tours", return_value=[activity_tours[0]])
    mocker.patch.object(MoveActivityTourToHomeLocation, "tour_matches_activities")
    MoveActivityTourToHomeLocation([""]).matching_activity_tours(Plan(1), plain_filter)

    MoveActivityTourToHomeLocation.tour_matches_activities.assert_called_once_with(
        activity_tours[0], plain_filter
    )


def test_matching_activity_tours_matches_one_tour(mocker, activity_tours, plain_filter):
    mocker.patch.object(Plan, "activity_tours", return_value=activity_tours)
    mocker.patch.object(
        MoveActivityTourToHomeLocation, "tour_matches_activities", side_effect=[True, False]
    )

    matching_tours = MoveActivityTourToHomeLocation([""]).matching_activity_tours(
        Plan(1), plain_filter
    )

    assert matching_tours == [activity_tours[0]]


def test_tour_matches_activities_returns_True_when_there_is_a_matching_tour_and_plain_filter(
    activity_tours, plain_filter
):
    assert MoveActivityTourToHomeLocation(["education", "shop"]).tour_matches_activities(
        activity_tours[0], plain_filter
    )


def test_tour_matches_activities_returns_True_when_there_is_a_matching_tour_and_individual_filter(
    activity_tours,
):
    def is_a_selected_activity(act):
        for other_act in activity_tours[0]:
            if act.is_exact(other_act):
                return True
        return False

    assert MoveActivityTourToHomeLocation(["education", "shop"]).tour_matches_activities(
        activity_tours[0], is_a_selected_activity
    )


def test_tour_matches_activities_returns_False_when_there_is_no_matching_tour_and_plain_filter(
    activity_tours, plain_filter
):
    assert not MoveActivityTourToHomeLocation(["education", "shop"]).tour_matches_activities(
        activity_tours[1], plain_filter
    )


def test_activity_is_part_of_tour(activity_tours):
    activity_in_tour = activity_tours[0][0]
    assert MoveActivityTourToHomeLocation([""]).is_part_of_tour(activity_in_tour, activity_tours)


def test_activity_is_not_part_of_tour(activity_tours):
    activity_not_in_tour = Activity(0, "blah", "bleh")
    assert not MoveActivityTourToHomeLocation([""]).is_part_of_tour(
        activity_not_in_tour, activity_tours
    )


def test_is_part_of_tour_delegates_to_is_exact_method(mocker):
    mocker.patch.object(Activity, "is_exact")
    a = Activity(1)
    b = Activity(2)
    MoveActivityTourToHomeLocation([""]).is_part_of_tour(a, [[b]])

    Activity.is_exact.assert_called_once_with(b)
