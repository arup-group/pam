import pytest
from shapely.geometry import Point
from datetime import datetime

from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt

EOD = datetime(1900, 1, 1, 23, 59, 59)


@pytest.fixture
def person_heh():

    person = Person('1')
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
def person_crop_last_act():

    person = Person('1')
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
def person_crop_last_leg():

    person = Person('1')
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
            end_time=mtdt(2600)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(2600),
            end_time=mtdt(3000)
        )
    )

    return person


@pytest.fixture
def population_heh():
    home_loc = Point(0,0)
    education_loc = Point(110,110)
    attributes = {
        'hid': 0,
        'hh_size': 3,
        'inc': "high"
    }
    person = Person('1', attributes=attributes)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            loc = home_loc,
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
            loc=education_loc,
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
            loc=home_loc,
            start_time=mtdt(180),
            end_time=EOD
        )
    )
    person.plan.autocomplete_matsim()
    household = Household('0')
    household.add(person)
    population = Population()
    population.add(household)
    return population


@pytest.fixture
def person_heh_open1():

    person = Person('1')
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
            area='b',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_hew_open2():

    person = Person('1')
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
            act='work',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_whw():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            act='work',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_whshw():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            end_area='c',
            start_time=mtdt(120),
            end_time=mtdt(190)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='shop',
            area='c',
            start_time=mtdt(190),
            end_time=mtdt(220)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='c',
            end_area='b',
            start_time=mtdt(220),
            end_time=mtdt(280)
        )
    )
    person.add(
        Activity(
            seq=4,
            act='home',
            area='b',
            start_time=mtdt(280),
            end_time=mtdt(320)
        )
    )
    person.add(
        Leg(
            seq=4,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(320),
            end_time=mtdt(380)
        )
    )
    person.add(
        Activity(
            seq=5,
            act='work',
            area='a',
            start_time=mtdt(380),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_home_education_home():

    person = Person('1')
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
def person_work_home_work_closed():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            act='work',
            area='a',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_work_home_shop_home_work_closed():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            end_area='c',
            start_time=mtdt(120),
            end_time=mtdt(190)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='shop',
            area='c',
            start_time=mtdt(190),
            end_time=mtdt(220)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='c',
            end_area='b',
            start_time=mtdt(220),
            end_time=mtdt(280)
        )
    )
    person.add(
        Activity(
            seq=4,
            act='home',
            area='b',
            start_time=mtdt(280),
            end_time=mtdt(320)
        )
    )
    person.add(
        Leg(
            seq=4,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(320),
            end_time=mtdt(380)
        )
    )
    person.add(
        Activity(
            seq=5,
            act='work',
            area='a',
            start_time=mtdt(380),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_work_home_shop_home_work_not_closed():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            end_area='c',
            start_time=mtdt(120),
            end_time=mtdt(190)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='shop',
            area='c',
            start_time=mtdt(190),
            end_time=mtdt(220)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='c',
            end_area='d',
            start_time=mtdt(220),
            end_time=mtdt(280)
        )
    )
    person.add(
        Activity(
            seq=4,
            act='home',
            area='d',
            start_time=mtdt(280),
            end_time=mtdt(320)
        )
    )
    person.add(
        Leg(
            seq=4,
            mode='car',
            start_area='d',
            end_area='a',
            start_time=mtdt(320),
            end_time=mtdt(380)
        )
    )
    person.add(
        Activity(
            seq=5,
            act='work',
            area='a',
            start_time=mtdt(380),
            end_time=EOD
        )
    )

    return person


@pytest.fixture
def person_work_home_work_not_closed():

    person = Person('1')
    person.add(
        Activity(
            seq=1,
            act='work',
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
            act='home',
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
            end_area='c',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='work',
            area='c',
            start_time=mtdt(180),
            end_time=EOD
        )
    )

    return person

