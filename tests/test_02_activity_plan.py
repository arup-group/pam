from datetime import timedelta

import pytest
from pam import PAMSequenceValidationError
from pam.activity import Activity, Leg, Location, Plan
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def test_plan_init():
    plan = Plan()
    assert not plan.day


def test_home(person_heh):
    assert person_heh.plan.home == Location(area="a")


def test_activities(person_heh):
    assert [a.act for a in person_heh.plan.activities] == ["home", "education", "home"]


def test_legs(person_heh):
    assert [leg.mode for leg in person_heh.plan.legs] == ["car", "car"]


def test_closed(person_heh):
    assert person_heh.plan.closed is True


def test_not_closed_due_to_location(person_heh_open1):
    assert person_heh_open1.plan.closed is False


def test_not_closed_due_to_act(person_hew_open2):
    assert person_hew_open2.plan.closed is False


def test_select_first(person_hew_open2):
    assert person_hew_open2.plan.first == "home"


def test_select_last(person_hew_open2):
    assert person_hew_open2.plan.last == "work"


def test_home_based(person_heh):
    assert person_heh.plan.home_based is True


def test_length(person_heh, person_whshw):
    assert person_heh.plan.length == 5
    assert person_whshw.plan.length == 9


def test_position_of(person_whshw):
    assert person_whshw.plan.position_of(target="home") == 6
    assert person_whshw.plan.position_of(target="home", search="first") == 2


def test_person_add_activity():
    plan = Plan()
    act = Activity(1, "home", 1)
    plan.add(act)
    assert len(plan.day) == 1


def test_person_add_leg():
    plan = Plan()
    act = Activity(1, "home", 1)
    plan.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2)
    plan.add(leg)
    assert len(plan.day) == 2


def test_person_add_activity_activity_raise_error():
    plan = Plan()
    act = Activity(1, "home", 1)
    plan.add(act)
    act = Activity(2, "work", 1)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(act)


def test_person_add_leg_first_raise_error():
    plan = Plan()
    leg = Leg(1, "car", start_area=1, end_area=2)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(leg)


def test_person_add_leg_leg_raise_error():
    plan = Plan()
    act = Activity(1, "home", 1)
    plan.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2)
    plan.add(leg)
    leg = Leg(2, "car", start_area=2, end_area=1)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(leg)


def test_finalise():
    plan = Plan()
    act = Activity(1, "home", 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, "work", 1, start_time=mtdt(930))
    plan.add(act)
    plan.finalise_activity_end_times()
    assert plan.day[0].end_time == mtdt(900)
    assert plan.day[-1].end_time == END_OF_DAY


def test_reverse_iter():
    plan = Plan()
    act = Activity(1, "home", 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, "work", 1, start_time=mtdt(930))
    plan.add(act)
    idxs = list(i for i, c in plan.reversed())
    assert idxs == [2, 1, 0]


@pytest.fixture()
def activities_and_tour():
    a_1 = Activity(1, "home", "a")
    a_2 = Activity(2, "shop", "a")
    a_3 = Activity(3, "education", "b")
    a_4 = Activity(4, "home", "a")
    a_5 = Activity(5, "shop", "d")
    a_6 = Activity(6, "work", "d")
    a_7 = Activity(7, "home", "d")
    return {"activities": [a_1, a_2, a_3, a_4, a_5, a_6, a_7], "tours": [[a_2, a_3], [a_5, a_6]]}


def test_activity_tours_segments_home_to_home_looped_plan(activities_and_tour):
    plan = Plan(1)
    for i in range(len(activities_and_tour["activities"]) - 1):
        plan.add(activities_and_tour["activities"][i])
        plan.add(Leg(1))
    plan.add(activities_and_tour["activities"][-1])
    assert plan.activity_tours() == activities_and_tour["tours"]


def test_activity_tours_segments_home_to_other_act_nonlooped_plan(activities_and_tour):
    plan = Plan(1)
    for i in range(len(activities_and_tour["activities"])):
        plan.add(activities_and_tour["activities"][i])
        plan.add(Leg(1))
    other_act = Activity(8, "other", "e")
    plan.add(other_act)

    assert plan[0].act != plan[-1].act

    assert plan.activity_tours() == activities_and_tour["tours"] + [[other_act]]


def test_activity_tours_segments_home_to_other_act_nonhome_looped_plan(activities_and_tour):
    other_act = Activity(8, "other", "e")

    plan = Plan(1)
    plan.add(other_act)
    plan.add(Leg(1))
    for i in range(len(activities_and_tour["activities"])):
        plan.add(activities_and_tour["activities"][i])
        plan.add(Leg(1))
    plan.add(other_act)

    assert plan[0].act == plan[-1].act
    assert plan.activity_tours() == [[other_act]] + activities_and_tour["tours"] + [[other_act]]


# trip yields
def test_yield_trips_from_legs_simple():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
            distance=1000,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trips())
    assert [t.mode for t in trips] == ["car", "bike"]
    assert [t.purp for t in trips] == ["shop", "home"]
    assert [t.start_time for t in trips] == [mtdt(600), mtdt(1200)]
    assert [t.end_time for t in trips] == [mtdt(620), mtdt(1220)]
    assert [t.start_location.area for t in trips] == ["A", "B"]
    assert [t.end_location.area for t in trips] == ["B", "A"]
    assert [t.distance for t in trips] == [1000, 1000]


def test_yield_trips_from_legs_with_transit():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="A",
            end_area="A",
            start_time=mtdt(600),
            end_time=mtdt(602),
            distance=100,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(602), end_time=mtdt(602))
    )
    plan.add(
        Leg(
            seq=2,
            mode="bus",
            start_area="A",
            end_area="B",
            start_time=mtdt(602),
            end_time=mtdt(618),
            distance=800,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="B", start_time=mtdt(618), end_time=mtdt(618))
    )
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="B",
            end_area="B",
            start_time=mtdt(618),
            end_time=mtdt(620),
            distance=100,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trips())
    assert [t.mode for t in trips] == ["bus", "bike"]
    assert [t.purp for t in trips] == ["shop", "home"]
    assert [t.start_time for t in trips] == [mtdt(600), mtdt(1200)]
    assert [t.end_time for t in trips] == [mtdt(620), mtdt(1220)]
    assert [t.start_location.area for t in trips] == ["A", "B"]
    assert [t.end_location.area for t in trips] == ["B", "A"]
    assert [t.distance for t in trips] == [1000, 1000]


def test_yield_trips_from_legs_with_complex_transit():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="A",
            end_area="A",
            start_time=mtdt(600),
            end_time=mtdt(602),
            distance=100,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(602), end_time=mtdt(602))
    )
    plan.add(
        Leg(
            seq=2,
            mode="bus",
            start_area="A",
            end_area="B",
            start_time=mtdt(602),
            end_time=mtdt(610),
            distance=300,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(610), end_time=mtdt(610))
    )
    plan.add(
        Leg(
            seq=2,
            mode="rail",
            start_area="A",
            end_area="B",
            start_time=mtdt(610),
            end_time=mtdt(618),
            distance=500,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="B", start_time=mtdt(618), end_time=mtdt(618))
    )
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="B",
            end_area="B",
            start_time=mtdt(618),
            end_time=mtdt(620),
            distance=100,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trips())
    assert [t.mode for t in trips] == ["rail", "bike"]
    assert [t.purp for t in trips] == ["shop", "home"]
    assert [t.start_time for t in trips] == [mtdt(600), mtdt(1200)]
    assert [t.end_time for t in trips] == [mtdt(620), mtdt(1220)]
    assert [t.start_location.area for t in trips] == ["A", "B"]
    assert [t.end_location.area for t in trips] == ["B", "A"]
    assert [t.distance for t in trips] == [1000, 1000]


def test_yield_trips_from_legs_empty():
    plan = Plan()
    assert list(plan.trips()) == []


# trip leg yields
def test_yield_trip_legs_from_legs_simple():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
            distance=1000,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trip_legs())
    assert [len(trip) for trip in trips] == [1, 1]
    assert [leg.mode for trip in trips for leg in trip] == ["car", "bike"]


def test_yield_trip_legs_from_legs_with_transit():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="A",
            end_area="A",
            start_time=mtdt(600),
            end_time=mtdt(602),
            distance=100,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(602), end_time=mtdt(602))
    )
    plan.add(
        Leg(
            seq=2,
            mode="bus",
            start_area="A",
            end_area="B",
            start_time=mtdt(602),
            end_time=mtdt(618),
            distance=800,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="B", start_time=mtdt(618), end_time=mtdt(618))
    )
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="B",
            end_area="B",
            start_time=mtdt(618),
            end_time=mtdt(620),
            distance=100,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trip_legs())
    assert [len(trip) for trip in trips] == [3, 1]
    assert [leg.mode for trip in trips for leg in trip] == ["walk", "bus", "walk", "bike"]


def test_yield_trip_legs_from_legs_with_complex_transit():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="A",
            end_area="A",
            start_time=mtdt(600),
            end_time=mtdt(602),
            distance=100,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(602), end_time=mtdt(602))
    )
    plan.add(
        Leg(
            seq=2,
            mode="bus",
            start_area="A",
            end_area="B",
            start_time=mtdt(602),
            end_time=mtdt(610),
            distance=300,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="A", start_time=mtdt(610), end_time=mtdt(610))
    )
    plan.add(
        Leg(
            seq=2,
            mode="rail",
            start_area="A",
            end_area="B",
            start_time=mtdt(610),
            end_time=mtdt(618),
            distance=500,
        )
    )
    plan.add(
        Activity(seq=1, act="pt interaction", area="B", start_time=mtdt(618), end_time=mtdt(618))
    )
    plan.add(
        Leg(
            seq=2,
            mode="walk",
            start_area="B",
            end_area="B",
            start_time=mtdt(618),
            end_time=mtdt(620),
            distance=100,
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    plan.add(
        Leg(
            seq=4,
            mode="bike",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
            distance=1000,
        )
    )
    plan.add(Activity(seq=5, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))
    trips = list(plan.trip_legs())
    assert [len(trip) for trip in trips] == [4, 1]
    assert [leg.mode for trip in trips for leg in trip] == ["walk", "bus", "rail", "walk", "bike"]


def test_yield_trip_legs_from_legs_empty():
    plan = Plan()
    assert list(plan.trip_legs()) == []


def test_move_activity_with_home_default():
    plan = Plan("a")
    plan.add(Activity(1, "home", area="a"))
    plan.add(Leg(1))
    plan.add(Activity(2, "shop", area="b"))
    plan.add(Leg(2))
    plan.add(Activity(3, "home", area="a"))

    plan.move_activity(2)

    assert plan[2].location.area == "a"


def test_move_activity_with_home_default_updates_legs():
    plan = Plan("a")
    plan.add(Activity(1, "home", area="a"))
    plan.add(Leg(1))
    plan.add(Activity(2, "shop", area="b"))
    plan.add(Leg(2))
    plan.add(Activity(3, "home", area="a"))

    plan.move_activity(2)

    assert plan[1].end_location.area == "a"
    assert plan[3].start_location.area == "a"


def test_move_activity_with_different_default():
    plan = Plan("a")
    plan.add(Activity(1, "home", area="a"))
    plan.add(Leg(1))
    plan.add(Activity(2, "shop", area="b"))
    plan.add(Leg(2))
    plan.add(Activity(3, "home", area="a"))

    new_loc = Location(area="heyooo")
    plan.move_activity(2, default=new_loc)

    assert plan[2].location == new_loc


def test_move_activity_with_different_default_updates_legs():
    plan = Plan("a")
    plan.add(Activity(1, "home", area="a"))
    plan.add(Leg(1))
    plan.add(Activity(2, "shop", area="b"))
    plan.add(Leg(2))
    plan.add(Activity(3, "home", area="a"))

    new_loc = Location(area="heyooo")
    plan.move_activity(2, default=new_loc)

    assert plan[1].end_location == new_loc
    assert plan[3].start_location == new_loc


def test_move_activity_at_start_of_plan_updates_leg():
    plan = Plan("a")
    plan.add(Activity(1, "shop", area="b"))
    plan.add(Leg(1))
    plan.add(Activity(2, "home", area="a"))

    plan.move_activity(0)

    assert plan[1].start_location == "a"


def test_move_activity_at_end_of_plan_updates_leg():
    plan = Plan("a")
    plan.add(Activity(1, "home", area="a"))
    plan.add(Leg(1))
    plan.add(Activity(2, "shop", area="b"))

    plan.move_activity(2)

    assert plan[1].end_location == "a"


def test_mode_shift_single_tour():
    plan = Plan("a")
    plan.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(Leg(1, mode="car", start_time=mtdt(60), end_time=mtdt(90)))
    plan.add(Activity(2, "shop", "b", start_time=mtdt(90), end_time=mtdt(500)))
    plan.add(Leg(2, mode="car", start_time=mtdt(500), end_time=mtdt(400)))
    plan.add(Activity(3, "home", "a", start_time=mtdt(400), end_time=mtdt(24 * 60 - 1)))

    plan.mode_shift(1, "pt")

    assert [leg.mode for leg in plan.legs] == ["pt", "pt"]


def test_mode_shift_two_tours_first_leg():
    plan = Plan("a")
    plan.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(Leg(1, mode="car", start_time=mtdt(60), end_time=mtdt(90)))
    plan.add(Activity(2, "shop", "b", start_time=mtdt(90), end_time=mtdt(500)))
    plan.add(Leg(2, mode="car", start_time=mtdt(500), end_time=mtdt(400)))
    plan.add(Activity(3, "home", "a", start_time=mtdt(400), end_time=mtdt(860)))
    plan.add(Leg(3, mode="car", start_time=mtdt(860), end_time=mtdt(900)))
    plan.add(Activity(4, "work", "a", start_time=mtdt(920), end_time=mtdt(930)))
    plan.add(Leg(4, mode="car", start_time=mtdt(930), end_time=mtdt(1000)))
    plan.add(Activity(5, "home", "a", start_time=mtdt(1000), end_time=mtdt(24 * 60 - 1)))

    plan.mode_shift(1, "pt")

    assert [leg.mode for leg in plan.legs] == ["pt", "pt", "car", "car"]


def test_mode_shift_two_tours_second_leg():
    plan = Plan("a")
    plan.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(Leg(1, mode="car", start_time=mtdt(60), end_time=mtdt(90)))
    plan.add(Activity(2, "shop", "b", start_time=mtdt(90), end_time=mtdt(500)))
    plan.add(Leg(2, mode="car", start_time=mtdt(500), end_time=mtdt(400)))
    plan.add(Activity(3, "home", "a", start_time=mtdt(400), end_time=mtdt(860)))
    plan.add(Leg(3, mode="car", start_time=mtdt(860), end_time=mtdt(900)))
    plan.add(Activity(4, "work", "a", start_time=mtdt(920), end_time=mtdt(930)))
    plan.add(Leg(4, mode="car", start_time=mtdt(930), end_time=mtdt(1000)))
    plan.add(Activity(5, "home", "a", start_time=mtdt(1000), end_time=mtdt(24 * 60 - 1)))

    plan.mode_shift(3, "pt")

    assert [leg.mode for leg in plan.legs] == ["pt", "pt", "car", "car"]


def test_mode_shift_two_tours_third_leg():
    plan = Plan("a")
    plan.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(Leg(1, mode="car", start_time=mtdt(60), end_time=mtdt(90)))
    plan.add(Activity(2, "shop", "b", start_time=mtdt(90), end_time=mtdt(500)))
    plan.add(Leg(2, mode="car", start_time=mtdt(500), end_time=mtdt(400)))
    plan.add(Activity(3, "home", "a", start_time=mtdt(400), end_time=mtdt(860)))
    plan.add(Leg(3, mode="car", start_time=mtdt(860), end_time=mtdt(900)))
    plan.add(Activity(4, "work", "a", start_time=mtdt(920), end_time=mtdt(930)))
    plan.add(Leg(4, mode="car", start_time=mtdt(930), end_time=mtdt(1000)))
    plan.add(Activity(5, "home", "a", start_time=mtdt(1000), end_time=mtdt(24 * 60 - 1)))

    plan.mode_shift(5, "pt")

    assert [leg.mode for leg in plan.legs] == ["car", "car", "pt", "pt"]


def test_mode_shift_multiple_tours():
    plan = Plan("a")
    plan.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(Leg(1, mode="car", start_time=mtdt(60), end_time=mtdt(90)))
    plan.add(Activity(2, "work", "b", start_time=mtdt(90), end_time=mtdt(500)))
    plan.add(Leg(2, mode="car", start_time=mtdt(500), end_time=mtdt(400)))
    plan.add(Activity(3, "shop", "b", start_time=mtdt(400), end_time=mtdt(450)))
    plan.add(Leg(3, mode="car", start_time=mtdt(450), end_time=mtdt(600)))
    plan.add(Activity(4, "work", "b", start_time=mtdt(600), end_time=mtdt(660)))
    plan.add(Leg(4, mode="car", start_time=mtdt(660), end_time=mtdt(800)))
    plan.add(Activity(5, "home", "a", start_time=mtdt(830), end_time=mtdt(860)))
    plan.add(Leg(5, mode="walk", start_time=mtdt(860), end_time=mtdt(900)))
    plan.add(Activity(6, "other", "a", start_time=mtdt(900), end_time=mtdt(920)))
    plan.add(Leg(6, mode="walk", start_time=mtdt(920), end_time=mtdt(950)))
    plan.add(Activity(7, "home", "a", start_time=mtdt(950), end_time=mtdt(24 * 60 - 1)))

    plan.mode_shift(5, "pt")

    assert [leg.mode for leg in plan.legs] == ["pt", "pt", "pt", "pt", "walk", "walk"]


def test_leg_duration():
    plan = Plan("a")
    plan.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    plan.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    plan.add(Activity(seq=2, act="work", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )

    plan.add(
        Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=mtdt(24 * 60 - 1))
    )

    plan.mode_shift(
        3,
        "rail",
        mode_speed={"car": 37, "bus": 10, "walk": 4, "cycle": 14, "pt": 23, "rail": 37},
        update_duration=True,
    )

    assert [act.duration for act in plan] == [
        timedelta(seconds=3603),
        timedelta(seconds=1800),
        timedelta(seconds=1800),
        timedelta(seconds=3600),
        timedelta(seconds=75597),
    ]
