import pytest
from datetime import datetime

from pam.core import Population, Household, Person, Activity, Leg, minutes_to_datetime


testdata = [
    (0, datetime(2020, 4, 2, 0, 0)),
    (30, datetime(2020, 4, 2, 0, 30)),
    (300, datetime(2020, 4, 2, 5, 0)),
    (330, datetime(2020, 4, 2, 5, 30)),
]


@pytest.mark.parametrize("m,expected", testdata)
def test_minutes_to_dt(m, expected):
    assert minutes_to_datetime(m) == expected


def test_population_add_household():
    population = Population()
    household = Household(1)
    population.add(household)
    assert len(population.households) == 1
    assert list(population.households) == [1]


def test_household_add_person():
    household = Household(1)
    person = Person(1)
    person.add(Activity(1, 'home', 1, start_time=0))
    household.add(person)
    assert len(household.people) == 1
    assert list(household.people) == [1]


def test_person_add_activity():
    person = Person(1)
    act = Activity(1, 'home', 1)
    person.add(act)
    assert len(person.plan) == 1


def test_person_add_leg():
    person = Person(1)
    act = Activity(1, 'home', 1)
    person.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2)
    person.add(leg)
    assert len(person.plan) == 2


def test_person_add_activity_activity_raise_error():
    person = Person(1)
    act = Activity(1, 'home', 1)
    person.add(act)
    act = Activity(2, 'work', 1)
    with pytest.raises(UserWarning):
        person.add(act)


def test_person_add_leg_first_raise_error():
    person = Person(1)
    leg = Leg(1, 'car', start_area=1, end_area=2)
    with pytest.raises(UserWarning):
        person.add(leg)


def test_person_add_leg_leg_raise_error():
    person = Person(1)
    act = Activity(1, 'home', 1)
    person.add(act)
    leg = Leg(1, 'car', start_area=1, end_area=2)
    person.add(leg)
    leg = Leg(2, 'car', start_area=2, end_area=1)
    with pytest.raises(UserWarning):
        person.add(leg)


def test_person_home_based():
    person = Person(1)
    person.add(Activity(1, 'home', 1))
    person.add(Leg(1, 'car', start_area=1, end_area=2))
    person.add(Activity(2, 'work', 1))
    person.add(Leg(2, 'car', start_area=2, end_area=1))
    person.add(Activity(3, 'home', 1))
    assert person.home_based


def test_person_not_home_based():
    person = Person(1)
    person.add(Activity(1, 'work', 1))
    person.add(Leg(1, 'car', start_area=1, end_area=2))
    person.add(Activity(2, 'home', 1))
    person.add(Leg(2, 'car', start_area=2, end_area=1))
    person.add(Activity(3, 'work', 1))
    assert not person.home_based


def test_person_closed_plan():
    person = Person(1)
    person.add(Activity(1, 'home', 1))
    person.add(Leg(1, 'car', start_area=1, end_area=2))
    person.add(Activity(2, 'work', 1))
    person.add(Leg(2, 'car', start_area=2, end_area=1))
    person.add(Activity(3, 'home', 1))
    assert person.closed_plan


def test_person_not_closed_plan_different_acts():
    person = Person(1)
    person.add(Activity(1, 'work', 1))
    person.add(Leg(1, 'car', start_area=1, end_area=2))
    person.add(Activity(2, 'home', 1))
    assert not person.closed_plan


def test_person_not_closed_plan_different_areas():
    person = Person(1)
    person.add(Activity(1, 'work', 1))
    person.add(Leg(1, 'car', start_area=1, end_area=2))
    person.add(Activity(2, 'home', 1))
    person.add(Leg(2, 'car', start_area=2, end_area=3))
    person.add(Activity(3, 'work', 3))
    assert not person.closed_plan


def test_activity_equal():
    assert Activity(1, 'work', 1) == Activity(3, 'work', 1)


def test_activity_not_equal_areas():
    assert not Activity(1, 'work', 2) == Activity(3, 'work', 1)


def test_activity_not_equal_acts():
    assert not Activity(1, 'home', 2) == Activity(3, 'work', 2)


@pytest.fixture
def person_home_education_home():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=minutes_to_datetime(0),
            end_time=minutes_to_datetime(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=minutes_to_datetime(120),
            end_time=minutes_to_datetime(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=minutes_to_datetime(180),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )

    return person


@pytest.fixture
def person_work_home_work_closed():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='work',
            area='a',
            start_time=minutes_to_datetime(0),
            end_time=minutes_to_datetime(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='home',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=minutes_to_datetime(120),
            end_time=minutes_to_datetime(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='work',
            area='a',
            start_time=minutes_to_datetime(180),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )

    return person


@pytest.fixture
def person_work_home_shop_home_work_closed():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='work',
            area='a',
            start_time=minutes_to_datetime(0),
            end_time=minutes_to_datetime(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='home',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='c',
            start_time=minutes_to_datetime(120),
            end_time=minutes_to_datetime(190)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='shop',
            area='c',
            start_time=minutes_to_datetime(190),
            end_time=minutes_to_datetime(220)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='c',
            end_area='b',
            start_time=minutes_to_datetime(220),
            end_time=minutes_to_datetime(280)
        )
    )
    person.add(
        Activity(
            seq=4,
            act='home',
            area='b',
            start_time=minutes_to_datetime(280),
            end_time=minutes_to_datetime(320)
        )
    )
    person.add(
        Leg(
            seq=4,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=minutes_to_datetime(320),
            end_time=minutes_to_datetime(380)
        )
    )
    person.add(
        Activity(
            seq=5,
            act='work',
            area='a',
            start_time=minutes_to_datetime(380),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )

    return person


@pytest.fixture
def person_work_home_shop_home_work_not_closed():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='work',
            area='a',
            start_time=minutes_to_datetime(0),
            end_time=minutes_to_datetime(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='home',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='c',
            start_time=minutes_to_datetime(120),
            end_time=minutes_to_datetime(190)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='shop',
            area='c',
            start_time=minutes_to_datetime(190),
            end_time=minutes_to_datetime(220)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='c',
            end_area='d',
            start_time=minutes_to_datetime(220),
            end_time=minutes_to_datetime(280)
        )
    )
    person.add(
        Activity(
            seq=4,
            act='home',
            area='d',
            start_time=minutes_to_datetime(280),
            end_time=minutes_to_datetime(320)
        )
    )
    person.add(
        Leg(
            seq=4,
            mode='car',
            start_area='d',
            end_area='a',
            start_time=minutes_to_datetime(320),
            end_time=minutes_to_datetime(380)
        )
    )
    person.add(
        Activity(
            seq=5,
            act='work',
            area='a',
            start_time=minutes_to_datetime(380),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )

    return person


@pytest.fixture
def person_work_home_work_not_closed():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='work',
            area='a',
            start_time=minutes_to_datetime(0),
            end_time=minutes_to_datetime(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='home',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='c',
            start_time=minutes_to_datetime(120),
            end_time=minutes_to_datetime(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='work',
            area='c',
            start_time=minutes_to_datetime(180),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )

    return person

# Tests for removing activities from plans

def test_home_education_home_remove_activity_education(person_home_education_home):

    person = person_home_education_home
    p_idx, s_idx = person.remove_activity(2)
    assert p_idx == 0
    assert s_idx == 3
    assert [p.act for p in person.activities] == ['home', 'home']


def test_work_home_work_remove_first_activity_closed(person_work_home_work_closed):

    person = person_work_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx == 1
    assert s_idx == 1
    assert [p.act for p in person.activities] == ['home']


def test_work_home_work_remove_last_activity_closed(person_work_home_work_closed):

    person = person_work_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(4)
    assert p_idx == 1
    assert s_idx == 1
    assert [p.act for p in person.activities] == ['home']

def test_work_home_work_shop_remove_first_activity_closed(person_work_home_shop_home_work_closed):

    person = person_work_home_shop_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx == 5
    assert s_idx == 1
    assert [p.act for p in person.activities] == ['home', 'shop', 'home']


def test_work_home_work_shop_remove_last_activity_closed(person_work_home_shop_home_work_closed):

    person = person_work_home_shop_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(8)
    assert p_idx == 5
    assert s_idx == 1
    assert [p.act for p in person.activities] == ['home', 'shop', 'home']


def test_work_home_work_remove_first_activity_not_closed(person_work_home_work_not_closed):

    person = person_work_home_work_not_closed
    assert not person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx is None
    assert s_idx == 1
    assert [p.act for p in person.activities] == ['home', 'work']


def test_work_home_work_remove_last_activity_not_closed(person_work_home_work_not_closed):

    person = person_work_home_work_not_closed
    assert not person.closed_plan
    p_idx, s_idx = person.remove_activity(4)
    assert p_idx == 2
    assert s_idx is None
    assert [p.act for p in person.activities] == ['work', 'home']

# Tests for filling plans


def test_home_education_home_fill_activity(person_home_education_home):

    person = person_home_education_home
    p_idx, s_idx = person.remove_activity(2)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 1
    assert [p.act for p in person.activities] == ['home']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24*60-1)
    assert person.valid_plan


def test_work_home_work_fill_activity_closed(person_work_home_work_closed):

    person = person_work_home_work_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 1
    assert [p.act for p in person.activities] == ['home']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24 * 60 - 1)
    assert person.valid_plan


def test_work_home_shop_work_fill_activity_closed(person_work_home_shop_home_work_closed):

    person = person_work_home_shop_home_work_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 5
    assert [p.act for p in person.activities] == ['home', 'shop', 'home']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24 * 60 - 1)
    assert person.valid_plan


def test_work_home_work_fill_first_activity_not_closed(person_work_home_shop_home_work_not_closed):

    person = person_work_home_shop_home_work_not_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 5
    assert [p.act for p in person.activities] == ['home', 'shop', 'home']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24 * 60 - 1)
    assert person.valid_plan


def test_work_home_work_fill_mid_activity_not_closed(person_work_home_shop_home_work_not_closed):

    person = person_work_home_shop_home_work_not_closed
    duration = person.plan[2].duration
    p_idx, s_idx = person.remove_activity(6)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 7
    assert [p.act for p in person.activities] == ['work', 'home', 'shop', 'work']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24 * 60 - 1)
    assert person.plan[2].duration > duration  # todo fix bad test
    assert person.valid_plan


def test_work_home_work_add_first_activity_not_closed(person_work_home_work_not_closed):

    person = person_work_home_work_not_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 3
    assert [p.act for p in person.activities] == ['home', 'work']
    assert person.plan[0].start_time == minutes_to_datetime(0)
    assert person.plan[-1].end_time == minutes_to_datetime(24 * 60 - 1)
    assert person.valid_plan

