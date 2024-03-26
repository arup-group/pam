import pytest
from pam import PAMSequenceValidationError, PAMTimesValidationError, PAMValidationLocationsError
from pam.activity import Activity, Leg, Plan
from pam.core import Person
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def test_person_heh_valid_plan(person_heh):
    assert person_heh.plan.is_valid


def test_person_heh_open1_valid(person_heh_open1):
    assert person_heh_open1.has_valid_plan


def test_person_heh_open1_valid_plan(person_heh_open1):
    assert person_heh_open1.plan.is_valid


def test_person_hew_open1_valid(person_hew_open2):
    assert person_hew_open2.plan.is_valid


def test_person_whw_valid(person_whw):
    assert person_whw.plan.is_valid


def test_person_whshw_valid(person_whshw):
    assert person_whshw.plan.is_valid


@pytest.fixture
def act_act_sequence():
    person = Person("1")
    person.plan.day = [
        Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)),
        Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY),
    ]
    return person


def test_act_act_sequence_not_valid(act_act_sequence):
    with pytest.raises(PAMSequenceValidationError):
        act_act_sequence.plan.validate_sequence()


@pytest.fixture
def leg_leg_sequence():
    person = Person("1")
    person.plan.day = [
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(0), end_time=mtdt(90)),
        Leg(seq=2, mode="car", start_area="b", end_area="a", start_time=mtdt(0), end_time=mtdt(90)),
    ]
    return person


def test_leg_leg_sequence_not_valid(leg_leg_sequence):
    with pytest.raises(PAMSequenceValidationError):
        leg_leg_sequence.plan.validate_sequence()


@pytest.fixture
def act_leg_leg_act_plan():
    person = Person("1")
    person.plan.day = [
        Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)),
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(0), end_time=mtdt(90)),
        Leg(seq=1, mode="car", start_area="b", end_area="a", start_time=mtdt(0), end_time=mtdt(90)),
        Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY),
    ]
    return person


def test_act_leg_leg_act_sequence_not_valid(act_leg_leg_act_plan):
    with pytest.raises(PAMSequenceValidationError):
        act_leg_leg_act_plan.plan.validate_sequence()


@pytest.fixture
def act_leg_act_leg_act_bad_times():
    person = Person("1")
    person.plan.day = [
        Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)),
        Leg(
            seq=1,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(180),
            end_time=mtdt(190),
        ),
        Activity(seq=2, act="work", area="b", start_time=mtdt(0), end_time=mtdt(180)),
        Leg(
            seq=1,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(190),
            end_time=mtdt(390),
        ),
        Activity(seq=3, act="home", area="a", start_time=mtdt(280), end_time=END_OF_DAY),
    ]
    return person


def test_invalid_times(act_leg_act_leg_act_bad_times):
    assert act_leg_act_leg_act_bad_times.plan.validate_locations()
    with pytest.raises(PAMTimesValidationError):
        act_leg_act_leg_act_bad_times.plan.validate_times()


def test_invalid_times_not_start_at_zero():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="a", start_time=mtdt(10), end_time=mtdt(180)))
    assert not plan.valid_start_of_day_time


def test_invalid_times_not_end_at_end_of_day():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)))
    assert not plan.valid_end_of_day_time


@pytest.fixture
def act_leg_act_leg_act_bad_locations1():
    person = Person("1")
    person.plan.day = [
        Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)),
        Leg(
            seq=1,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(180),
            end_time=mtdt(190),
        ),
        Activity(seq=2, act="work", area="b", start_time=mtdt(190), end_time=mtdt(200)),
        Leg(
            seq=1,
            mode="car",
            start_area="a",
            end_area="a",
            start_time=mtdt(200),
            end_time=mtdt(390),
        ),
        Activity(seq=3, act="home", area="a", start_time=mtdt(390), end_time=END_OF_DAY),
    ]
    return person


def test_invalid_locations(act_leg_act_leg_act_bad_locations1):
    assert act_leg_act_leg_act_bad_locations1.plan.validate_times()
    with pytest.raises(PAMValidationLocationsError):
        act_leg_act_leg_act_bad_locations1.plan.validate_locations()


@pytest.fixture
def act_leg_act_leg_act_bad_locations2():
    person = Person("1")
    person.plan.day = [
        Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(180)),
        Leg(
            seq=1,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(180),
            end_time=mtdt(190),
        ),
        Activity(seq=2, act="work", area="b", start_time=mtdt(190), end_time=mtdt(200)),
        Leg(
            seq=1,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(200),
            end_time=mtdt(390),
        ),
        Activity(seq=3, act="home", area="b", start_time=mtdt(390), end_time=END_OF_DAY),
    ]
    return person


def test_invalid_locations2(act_leg_act_leg_act_bad_locations2):
    assert act_leg_act_leg_act_bad_locations2.plan.validate_times()
    with pytest.raises(PAMValidationLocationsError):
        act_leg_act_leg_act_bad_locations2.plan.validate_locations()


def test_invalid_not_end_with_act():
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
    assert not plan.valid_sequence


def test_validate_sequence(person_heh):
    assert person_heh.validate()
