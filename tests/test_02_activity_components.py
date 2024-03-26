from datetime import timedelta

import pytest
from pam.activity import Activity, Leg, Location, Plan
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def test_act_init():
    act = Activity()
    assert act.act is None


def test_leg_init():
    leg = Leg()
    assert leg.mode is None


def test_activity_equal():
    assert Activity(1, "work", 1) == Activity(3, "work", 1)


def test_activity_not_equal_areas():
    assert not Activity(1, "work", 2) == Activity(3, "work", 1)


def test_activity_not_equal_acts():
    assert not Activity(1, "home", 2) == Activity(3, "work", 2)


def test_duration():
    plan = Plan()
    act = Activity(1, "home", 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, "work", 1, start_time=mtdt(930))
    plan.add(act)
    plan.finalise_activity_end_times()
    assert plan.day[0].duration == timedelta(minutes=900)
    assert plan.day[1].duration == timedelta(minutes=30)
    assert plan.day[-1].duration == timedelta(seconds=(24 * 60 - 930) * 60)


def test_shift_start_time():
    act = Activity(1, "home", 1, start_time=mtdt(900), end_time=mtdt(930))
    assert act.shift_start_time(new_start_time=mtdt(910)) == mtdt(940)


def test_shift_end_time():
    act = Activity(1, "home", 1, start_time=mtdt(900), end_time=mtdt(930))
    assert act.shift_end_time(new_end_time=mtdt(920)) == mtdt(890)


@pytest.fixture
def test_plan():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)))
    plan.add(
        Leg(
            seq=1,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(180),
            end_time=mtdt(190),
        )
    )
    plan.add(Activity(seq=2, act="work", area="b", start_time=mtdt(190), end_time=mtdt(200)))
    plan.add(
        Leg(
            seq=1,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(200),
            end_time=mtdt(390),
        )
    )
    plan.add(Activity(seq=3, act="home", area="b", start_time=mtdt(390), end_time=END_OF_DAY))
    return plan


def test_position_of(test_plan):
    assert test_plan.position_of("work") == 2
    assert test_plan.position_of("home") == 4
    assert test_plan.position_of("home", search="first") == 0


def test_position_of_using_bad_option(test_plan):
    with pytest.raises(UserWarning):
        test_plan.position_of("home", search="spelling") == 1


def test_position_of_missing(test_plan):
    assert test_plan.position_of("play") is None


def test_location_gets():
    location = Location(loc=None, link=1, area=2)
    assert location.min == 1
    assert location.max == 2


def test_locations_equal():
    locationa = Location(loc=None, link=1, area=2)
    locationb = Location(loc=None, link=None, area=2)
    locationc = Location(loc=None, link=2, area=1)
    locationd = Location(loc=None, link=2, area=None)
    locatione = Location(loc=None, link=2, area=2)
    assert locationa == locationb
    assert locationc == locationd
    assert not locationb == locationc
    assert not locationa == locatione


def test_locations_equal_with_no_shared_location_type():
    locationb = Location(loc=None, link=None, area=2)
    locationd = Location(loc=None, link=2, area=None)
    with pytest.raises(UserWarning):
        assert not locationb == locationd


def test_plan_contains_empty():
    plan = Plan()
    assert Activity() not in plan


def test_plan_contains_true():
    plan = Plan()
    act = Activity(start_time=0, loc=0)
    plan.add(act)
    assert act in plan


def test_plan_contains_true_multiple():
    plan = Plan()
    act = Activity(start_time=0, loc=0)
    plan.add(act)
    plan.add(Leg())
    plan.add(Activity(start_time=1, loc=0))
    assert act in plan


def test_plan_contains_true_multiple_different_order():
    plan = Plan()
    plan.add(Activity(start_time=0, loc=0))
    plan.add(Leg())
    act = Activity(start_time=1, loc=0)
    plan.add(act)
    assert act in plan


def test_plan_contains_false():
    plan = Plan()
    act = Activity(start_time=0, loc=0)
    plan.add(act)
    act = Activity(start_time=0, loc=1)
    assert act not in plan
