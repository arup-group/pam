import pytest
from datetime import datetime

from pam.core import Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from .fixtures import person_heh, person_heh_open1, person_hew_open2, person_whw, person_whshw
from pam.variables import EOD
from pam import PAMSequenceValidationError


def test_person_heh_valid(person_heh):
    assert person_heh.plan.is_valid


def test_person_heh_open1_valid(person_heh_open1):
    assert person_heh_open1.plan.is_valid


def test_person_hew_open1_valid(person_hew_open2):
    assert person_hew_open2.plan.is_valid


def test_person_whw_valid(person_whw):
    assert person_whw.plan.is_valid


def test_person_whshw_valid(person_whshw):
    assert person_whshw.plan.is_valid


@pytest.fixture
def act_act_sequence():
    person = Person('1')
    person.plan.day = [
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(180)
        ),
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    ]
    return person

def test_act_act_sequence_not_valid(act_act_sequence):
    
    with pytest.raises(PAMSequenceValidationError):
        act_act_sequence.plan.validate_sequence()

    with pytest.raises(PAMSequenceValidationError):
        act_act_sequence.plan.validate_times()

    with pytest.raises(PAMSequenceValidationError):
        act_act_sequence.plan.validate_locations()


@pytest.fixture
def leg_leg_sequence():
    person = Person('1')
    person.plan.day = [
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(0),
            end_time=mtdt(90)
        ),
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(0),
            end_time=mtdt(90)
        )
    ]


def test_leg_leg_sequence_not_valid(leg_leg_sequence):
    with pytest.raises(PAMSequenceValidationError):
        leg_leg_sequence.plan.validate_sequence()


@pytest.fixture
def act_leg_leg_act_plan():
    person = Person('1')
    person.plan.day = [
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(180)
        ),
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(0),
            end_time=mtdt(90)
        ),
        Leg(
            seq=1,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(0),
            end_time=mtdt(90)
        )
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    ]
    with pytest.raises(PAMSequenceValidationError):
        person.plan.validate_sequence()