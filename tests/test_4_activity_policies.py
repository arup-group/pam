from pam.core import Population, HouseHold, Person, Activity, Leg, minutes_to_datetime
from pam import policies

import pytest


@pytest.fixture
def home_education_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_home_education_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_home_work_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'work', 'd'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_shop_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'b'))
    person.add(Activity(2, 'shop', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


def test_home_education_home_removal_of_education_act():

    household = HouseHold(1)
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
            start_loc='a',
            end_loc='b',
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
            start_loc='b',
            end_loc='a',
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
    household.add(person)

    policy = policies.RemoveEducationActivity(1)
    policy.apply_to(household)
    assert [p.act for p in household.people[1].activities] == ['home']
    assert household.people[1].plan[0].start_time == minutes_to_datetime(0)
    assert household.people[1].plan[0].end_time == minutes_to_datetime(24*60-1)


def test_home_education_home_education_home_removal_of_education_act():

    household = HouseHold(1)
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
            start_loc='a',
            end_loc='b',
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
            start_loc='b',
            end_loc='a',
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
            end_time=minutes_to_datetime(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_loc='a',
            end_loc='b',
            start_time=minutes_to_datetime(300),
            end_time=minutes_to_datetime(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=minutes_to_datetime(390),
            end_time=minutes_to_datetime(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_loc='b',
            end_loc='a',
            start_time=minutes_to_datetime(520),
            end_time=minutes_to_datetime(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=minutes_to_datetime(680),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )
    household.add(person)

    policy = policies.RemoveEducationActivity(1)
    policy.apply_to(household)
    assert [p.act for p in household.people[1].activities] == ['home']
    assert household.people[1].plan[0].start_time == minutes_to_datetime(0)
    assert household.people[1].plan[0].end_time == minutes_to_datetime(24*60-1)


def test_home_work_home_education_home_removal_of_education_act():

    household = HouseHold(1)
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
            start_loc='a',
            end_loc='b',
            start_time=minutes_to_datetime(60),
            end_time=minutes_to_datetime(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='work',
            area='b',
            start_time=minutes_to_datetime(90),
            end_time=minutes_to_datetime(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_loc='b',
            end_loc='a',
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
            end_time=minutes_to_datetime(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_loc='a',
            end_loc='b',
            start_time=minutes_to_datetime(300),
            end_time=minutes_to_datetime(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=minutes_to_datetime(390),
            end_time=minutes_to_datetime(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_loc='b',
            end_loc='a',
            start_time=minutes_to_datetime(520),
            end_time=minutes_to_datetime(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=minutes_to_datetime(680),
            end_time=minutes_to_datetime(24 * 60 - 1)
        )
    )
    household.add(person)

    policy = policies.RemoveEducationActivity(1)
    policy.apply_to(household)
    # assert [p.act for p in household.people[1].activities] == ['home', 'work', 'home']
    # assert household.people[1].plan[0].start_time == minutes_to_datetime(0)
    # assert household.people[1].plan[0].end_time == minutes_to_datetime(24*60-1)
