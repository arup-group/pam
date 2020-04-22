from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam import modify

import pytest
from datetime import datetime
from pam.variables import EOD


@pytest.fixture
def person_home_education_home():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

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


def test_home_education_home_removal_of_education_act(person_home_education_home):

    household = Household(1)
    person = person_home_education_home

    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[0].end_time == EOD


def test_home_education_home_education_home_removal_of_education_act():

    household = Household(1)
    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=mtdt(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(300),
            end_time=mtdt(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(390),
            end_time=mtdt(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(520),
            end_time=mtdt(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(680),
            end_time=EOD
        )
    )
    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[0].end_time == EOD


def test_home_work_home_education_home_removal_of_education_act():

    household = Household(1)
    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='work',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=mtdt(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(300),
            end_time=mtdt(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(390),
            end_time=mtdt(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(520),
            end_time=mtdt(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(680),
            end_time=EOD
        )
    )
    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home', 'work', 'home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[-1].end_time == EOD
