import pytest
from shapely.geometry import Point

from pam.activity import Activity, Leg
from pam.core import Population, Household, Person
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def instantiate_household_with(persons: list, hid=1):
    household = Household(hid)
    for person in persons:
        household.add(person)
    return household


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list, [a.act for a in person.plan.activities]
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan)-1].end_time == END_OF_DAY


@pytest.fixture()
def Steve():
    Steve = Person(1, attributes={'age': 50, 'job': 'work', 'gender': 'male'})
    Steve.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(5 * 60)))
    Steve.add(Leg(1, 'car', 'a', 'b', start_time=mtdt(5 * 60), end_time=mtdt(6 * 60)))
    Steve.add(Activity(2, 'work', 'b', start_time=mtdt(6 * 60), end_time=mtdt(12 * 60)))
    Steve.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 10)))
    Steve.add(Activity(3, 'leisure', 'c', start_time=mtdt(12 * 60 + 10), end_time=mtdt(13 * 60 - 10)))
    Steve.add(Leg(3, 'walk', 'c', 'b', start_time=mtdt(13 * 60 - 10), end_time=mtdt(13 * 60)))
    Steve.add(Activity(4, 'work', 'b', start_time=mtdt(13 * 60), end_time=mtdt(18 * 60)))
    Steve.add(Leg(4, 'car', 'b', 'a', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)))
    Steve.add(Activity(5, 'home', 'a', start_time=mtdt(19 * 60), end_time=END_OF_DAY))
    return Steve


@pytest.fixture()
def Hilda():
    Hilda = Person(2, attributes={'age': 45, 'job': 'influencer', 'gender': 'female'})
    Hilda.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Hilda.add(Activity(2, 'escort_education', 'b', start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Leg(1, 'pt', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, 'shop', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Hilda.add(Leg(2, 'pt', 'b', 'c', start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Hilda.add(Activity(3, 'leisure', 'c', start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20)))
    Hilda.add(Leg(3, 'pt', 'c', 'b', start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Hilda.add(Activity(2, 'escort_education', 'b', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    return Hilda


@pytest.fixture()
def Timmy():
    Timmy = Person(3, attributes={'age': 18, 'job': 'education', 'gender': 'male'})
    Timmy.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(10 * 60)))
    Timmy.add(Leg(1, 'bike', 'a', 'b', start_time=mtdt(10 * 60), end_time=mtdt(11 * 60)))
    Timmy.add(Activity(2, 'education', 'b', start_time=mtdt(11 * 60), end_time=mtdt(13 * 60)))
    Timmy.add(Leg(2, 'bike', 'b', 'c', start_time=mtdt(13 * 60), end_time=mtdt(13 * 60 + 5)))
    Timmy.add(Activity(3, 'shop', 'c', start_time=mtdt(13 * 60 + 5), end_time=mtdt(13 * 60 + 30)))
    Timmy.add(Leg(3, 'bike', 'c', 'b', start_time=mtdt(13 * 60 + 30), end_time=mtdt(13 * 60 + 35)))
    Timmy.add(Activity(4, 'education', 'b', start_time=mtdt(13 * 60 + 35), end_time=mtdt(15 * 60)))
    Timmy.add(Leg(4, 'bike', 'b', 'd', start_time=mtdt(15 * 60), end_time=mtdt(15 * 60 + 10)))
    Timmy.add(Activity(5, 'leisure', 'd', start_time=mtdt(15 * 60 + 10), end_time=mtdt(18 * 60)))
    Timmy.add(Leg(5, 'bike', 'd', 'a', start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Timmy.add(Activity(6, 'home', 'a', start_time=mtdt(18 * 60 + 20), end_time=END_OF_DAY))
    return Timmy


@pytest.fixture()
def Bobby():
    Bobby = Person(4, attributes={'age': 6, 'job': 'education', 'gender': 'non-binary'})
    Bobby.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobby.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobby.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobby.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobby.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    return Bobby


@pytest.fixture()
def SmithHousehold(Steve, Hilda, Timmy, Bobby):
    return instantiate_household_with([Steve, Hilda, Timmy, Bobby])


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
            end_time=END_OF_DAY
        )
    )

    return person


@pytest.fixture
def person_crop_last_act():

    person = Person('1', attributes={'old': True})
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
            end_time=END_OF_DAY
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
        'hid': '0',
        'hh_size': '3',
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
            end_time=END_OF_DAY
        )
    )
    person.plan.autocomplete_matsim()
    household = Household('0')
    household.add(person)
    population = Population('populus')
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
            end_area='b',
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
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
            end_time=END_OF_DAY
        )
    )

    return person

