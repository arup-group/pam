import pytest
from datetime import datetime

from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from .fixtures import person_heh, person_heh_open1, person_hew_open2, person_whw, person_whshw
from pam.variables import END_OF_DAY
from pam import PAMSequenceValidationError


def test_plan_init():
    plan = Plan()
    assert not plan.day


def test_home(person_heh):
    assert person_heh.plan.home == 'a'


def test_activities(person_heh):
    assert [a.act for a in person_heh.plan.activities] == ['home', 'education', 'home']


def test_legs(person_heh):
    assert [l.mode for l in person_heh.plan.legs] == ['car', 'car']


def test_closed(person_heh):
    assert person_heh.plan.closed is True


def test_not_closed_due_to_location(person_heh_open1):
    assert person_heh_open1.plan.closed is False


def test_not_closed_due_to_act(person_hew_open2):
    assert person_hew_open2.plan.closed is False


def test_select_first(person_hew_open2):
    assert person_hew_open2.plan.first == 'home'


def test_select_last(person_hew_open2):
    assert person_hew_open2.plan.last == 'work'


def test_home_based(person_heh):
    assert person_heh.plan.home_based is True


def test_length(person_heh, person_whshw):
    assert person_heh.plan.length == 5
    assert person_whshw.plan.length == 9


def test_position_of(person_whshw):
    assert person_whshw.plan.position_of(target='home') == 6
    assert person_whshw.plan.position_of(target='home', search='first') == 2


def test_person_add_activity():
    plan = Plan()
    act = Activity(1, 'home', 1)
    plan.add(act)
    assert len(plan.day) == 1


def test_person_add_leg():
    plan = Plan()
    act = Activity(1, 'home', 1)
    plan.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2)
    plan.add(leg)
    assert len(plan.day) == 2


def test_person_add_activity_activity_raise_error():
    plan = Plan()
    act = Activity(1, 'home', 1)
    plan.add(act)
    act = Activity(2, 'work', 1)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(act)


def test_person_add_leg_first_raise_error():
    plan = Plan()
    leg = Leg(1, 'car', start_area=1, end_area=2)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(leg)


def test_person_add_leg_leg_raise_error():
    plan = Plan()
    act = Activity(1, 'home', 1)
    plan.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2)
    plan.add(leg)
    leg = Leg(2, 'car', start_area=2, end_area=1)
    with pytest.raises(PAMSequenceValidationError):
        plan.add(leg)


def test_finalise():
    plan = Plan()
    act = Activity(1, 'home', 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, 'work', 1, start_time=mtdt(930))
    plan.add(act)
    plan.finalise()
    assert plan.day[0].end_time == mtdt(900)
    assert plan.day[-1].end_time == END_OF_DAY


def test_reverse_iter():
    plan = Plan()
    act = Activity(1, 'home', 1, start_time=mtdt(0))
    plan.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2, start_time=mtdt(900), end_time=mtdt(930))
    plan.add(leg)
    act = Activity(2, 'work', 1, start_time=mtdt(930))
    plan.add(act)
    idxs = list(i for i, c in plan.reversed())
    assert idxs == [2,1,0]

