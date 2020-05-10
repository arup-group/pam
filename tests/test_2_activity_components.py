import pytest
from datetime import timedelta

from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt


def test_act_init():
    act = Activity()
    assert act.act is None


def test_leg_init():
    leg = Leg()
    assert leg.mode is None


def test_activity_equal():
    assert Activity(1, 'work', 1) == Activity(3, 'work', 1)


def test_activity_not_equal_areas():
    assert not Activity(1, 'work', 2) == Activity(3, 'work', 1)


def test_activity_not_equal_acts():
    assert not Activity(1, 'home', 2) == Activity(3, 'work', 2)


def test_duration():
    plan = Plan()
    act = Activity(1, 'home', 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, 'work', 1, start_time=mtdt(930))
    plan.add(act)
    plan.finalise()
    assert plan.day[0].duration == timedelta(minutes=900)
    assert plan.day[1].duration == timedelta(minutes=30)
    assert plan.day[-1].duration == timedelta(seconds=(24*60-930)*60)


def test_shift_start_time():
    act = Activity(1, 'home', 1, start_time=mtdt(900), end_time=mtdt(930))
    assert act.shift_start_time(new_start_time=mtdt(910)) == mtdt(940)


def test_shift_end_time():
    act = Activity(1, 'home', 1, start_time=mtdt(900), end_time=mtdt(930))
    assert act.shift_end_time(new_end_time=mtdt(920)) == mtdt(890)
