from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

from pam import read
from pam.activity import Activity, Leg
from pam.core import Household, Person, Population
from pam.planner.od import OD
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY

TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_trips_path():
    return TEST_DATA_DIR / "test_matsim_plans.xml"


@pytest.fixture(scope="session")
def test_trips_pathv12():
    return TEST_DATA_DIR / "test_matsim_plansv12.xml"


@pytest.fixture(scope="session")
def test_experienced_pathv12():
    return TEST_DATA_DIR / "test_matsim_experienced_plans_v12.xml"


@pytest.fixture(scope="session")
def instantiate_household_with():
    def _instantiate_household_with(persons: list, hid=1):
        household = Household(hid)
        for person in persons:
            household.add(person)
        return household

    return _instantiate_household_with


@pytest.fixture(scope="session")
def assert_correct_activities():
    def _assert_correct_activities(person, ordered_activities_list):
        assert len(person.plan) % 2 == 1
        for i in range(0, len(person.plan), 2):
            assert isinstance(person.plan.day[i], Activity)
        assert [a.act for a in person.plan.activities] == ordered_activities_list, [
            a.act for a in person.plan.activities
        ]
        assert person.plan[0].start_time == mtdt(0)
        assert person.plan[len(person.plan) - 1].end_time == END_OF_DAY

    return _assert_correct_activities


@pytest.fixture()
def Steve():
    Steve = Person(1, attributes={"age": 50, "job": "work", "gender": "male"})
    Steve.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(5 * 60)))
    Steve.add(Leg(1, "car", "a", "b", start_time=mtdt(5 * 60), end_time=mtdt(6 * 60)))
    Steve.add(Activity(2, "work", "b", start_time=mtdt(6 * 60), end_time=mtdt(12 * 60)))
    Steve.add(Leg(2, "walk", "b", "c", start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 10)))
    Steve.add(
        Activity(3, "leisure", "c", start_time=mtdt(12 * 60 + 10), end_time=mtdt(13 * 60 - 10))
    )
    Steve.add(Leg(3, "walk", "c", "b", start_time=mtdt(13 * 60 - 10), end_time=mtdt(13 * 60)))
    Steve.add(Activity(4, "work", "b", start_time=mtdt(13 * 60), end_time=mtdt(18 * 60)))
    Steve.add(Leg(4, "car", "b", "a", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)))
    Steve.add(Activity(5, "home", "a", start_time=mtdt(19 * 60), end_time=END_OF_DAY))
    return Steve


@pytest.fixture()
def Hilda():
    Hilda = Person(2, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Hilda.add(
        Activity(
            2, "escort_education", "b", start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)
        )
    )
    Hilda.add(Leg(1, "pt", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Hilda.add(Leg(2, "pt", "b", "c", start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Hilda.add(
        Activity(3, "leisure", "c", start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20))
    )
    Hilda.add(Leg(3, "pt", "c", "b", start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Hilda.add(
        Activity(2, "escort_education", "b", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30))
    )
    Hilda.add(Leg(1, "walk", "a", "b", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    return Hilda


@pytest.fixture()
def Timmy():
    Timmy = Person(3, attributes={"age": 18, "job": "education", "gender": "male"})
    Timmy.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(10 * 60)))
    Timmy.add(Leg(1, "bike", "a", "b", start_time=mtdt(10 * 60), end_time=mtdt(11 * 60)))
    Timmy.add(Activity(2, "education", "b", start_time=mtdt(11 * 60), end_time=mtdt(13 * 60)))
    Timmy.add(Leg(2, "bike", "b", "c", start_time=mtdt(13 * 60), end_time=mtdt(13 * 60 + 5)))
    Timmy.add(Activity(3, "shop", "c", start_time=mtdt(13 * 60 + 5), end_time=mtdt(13 * 60 + 30)))
    Timmy.add(Leg(3, "bike", "c", "b", start_time=mtdt(13 * 60 + 30), end_time=mtdt(13 * 60 + 35)))
    Timmy.add(Activity(4, "education", "b", start_time=mtdt(13 * 60 + 35), end_time=mtdt(15 * 60)))
    Timmy.add(Leg(4, "bike", "b", "d", start_time=mtdt(15 * 60), end_time=mtdt(15 * 60 + 10)))
    Timmy.add(Activity(5, "leisure", "d", start_time=mtdt(15 * 60 + 10), end_time=mtdt(18 * 60)))
    Timmy.add(Leg(5, "bike", "d", "a", start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Timmy.add(Activity(6, "home", "a", start_time=mtdt(18 * 60 + 20), end_time=END_OF_DAY))
    return Timmy


@pytest.fixture()
def Bobby():
    Bobby = Person(4, attributes={"age": 6, "job": "education", "gender": "non-binary"})
    Bobby.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobby.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobby.add(Activity(2, "education", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobby.add(Leg(2, "walk", "b", "c", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobby.add(Activity(5, "home", "a", start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    return Bobby


@pytest.fixture()
def SmithHousehold(instantiate_household_with, Steve, Hilda, Timmy, Bobby):
    return instantiate_household_with([Steve, Hilda, Timmy, Bobby])


@pytest.fixture
def person_heh() -> Person:
    person = Person("1")
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_crop_last_act():
    person = Person("1", attributes={"old": True})
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_crop_last_leg():
    person = Person("1")
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(2600),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(2600), end_time=mtdt(3000)))

    return person


@pytest.fixture
def population_heh():
    home_loc = Point(0, 0)
    education_loc = Point(110, 110)
    attributes = {"hid": "0", "hh_size": "3", "inc": "high"}
    person = Person("1", attributes=attributes)
    person.add(
        Activity(seq=1, act="home", area="a", loc=home_loc, start_time=mtdt(0), end_time=mtdt(60))
    )
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(
        Activity(
            seq=2,
            act="education",
            area="b",
            loc=education_loc,
            start_time=mtdt(90),
            end_time=mtdt(120),
        )
    )
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(
        Activity(
            seq=3, act="home", area="a", loc=home_loc, start_time=mtdt(180), end_time=END_OF_DAY
        )
    )
    person.plan.autocomplete_matsim()
    household = Household("0")
    household.add(person)
    population = Population("populus")
    population.add(household)
    return population


@pytest.fixture
def person_heh_open1():
    person = Person("1")
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="b",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="b", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_hew_open2():
    person = Person("1")
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="work", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_whw():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="work", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_whshw():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="c",
            start_time=mtdt(120),
            end_time=mtdt(190),
        )
    )
    person.add(Activity(seq=3, act="shop", area="c", start_time=mtdt(190), end_time=mtdt(220)))
    person.add(
        Leg(
            seq=3,
            mode="car",
            start_area="c",
            end_area="b",
            start_time=mtdt(220),
            end_time=mtdt(280),
        )
    )
    person.add(Activity(seq=4, act="home", area="b", start_time=mtdt(280), end_time=mtdt(320)))
    person.add(
        Leg(
            seq=4,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(320),
            end_time=mtdt(380),
        )
    )
    person.add(Activity(seq=5, act="work", area="a", start_time=mtdt(380), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_home_education_home():
    person = Person("1")
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_work_home_work_closed():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="work", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_work_home_shop_home_work_closed():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="c",
            start_time=mtdt(120),
            end_time=mtdt(190),
        )
    )
    person.add(Activity(seq=3, act="shop", area="c", start_time=mtdt(190), end_time=mtdt(220)))
    person.add(
        Leg(
            seq=3,
            mode="car",
            start_area="c",
            end_area="b",
            start_time=mtdt(220),
            end_time=mtdt(280),
        )
    )
    person.add(Activity(seq=4, act="home", area="b", start_time=mtdt(280), end_time=mtdt(320)))
    person.add(
        Leg(
            seq=4,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(320),
            end_time=mtdt(380),
        )
    )
    person.add(Activity(seq=5, act="work", area="a", start_time=mtdt(380), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_work_home_shop_home_work_not_closed():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="c",
            start_time=mtdt(120),
            end_time=mtdt(190),
        )
    )
    person.add(Activity(seq=3, act="shop", area="c", start_time=mtdt(190), end_time=mtdt(220)))
    person.add(
        Leg(
            seq=3,
            mode="car",
            start_area="c",
            end_area="d",
            start_time=mtdt(220),
            end_time=mtdt(280),
        )
    )
    person.add(Activity(seq=4, act="home", area="d", start_time=mtdt(280), end_time=mtdt(320)))
    person.add(
        Leg(
            seq=4,
            mode="car",
            start_area="d",
            end_area="a",
            start_time=mtdt(320),
            end_time=mtdt(380),
        )
    )
    person.add(Activity(seq=5, act="work", area="a", start_time=mtdt(380), end_time=END_OF_DAY))

    return person


@pytest.fixture
def person_work_home_work_not_closed():
    person = Person("1")
    person.add(Activity(seq=1, act="work", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="home", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="c",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="work", area="c", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture()
def default_config():
    return {
        "mUM": 1,
        "utilityOfLineSwitch": -1,
        "performing": 6,
        "waiting": -1,
        "waitingPt": -2,
        "lateArrival": -18,
        "earlyDeparture": -1,
        "work": {
            "typicalDuration": "08:30:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
            "latestStartTime": "09:30:00",
            "earliestEndTime": "16:00:00",
            "minimalDuration": "08:00:00",
        },
        "education": {
            "typicalDuration": "06:00:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
            "minimalDuration": "01:00:00",
        },
        "home": {"typicalDuration": "12:00:00", "minimalDuration": "08:00:00"},
        "shop": {"typicalDuration": "00:30:00", "minimalDuration": "00:10:00"},
        "car": {
            "constant": -1,
            "dailyMonetaryConstant": -1,
            "dailyUtilityConstant": -1,
            "marginalUtilityOfDistance": -1,
            "marginalUtilityOfTravelling": -5,
            "monetaryDistanceRate": -0.0005,
        },
        "pt": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
        "bus": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
        "train": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
        "walk": {"marginalUtilityOfTravelling": -12},
        "bike": {"marginalUtilityOfTravelling": -12},
    }


@pytest.fixture()
def config():
    # includes the default name
    return {
        "default": {
            "mUM": 1,
            "utilityOfLineSwitch": -1,
            "performing": 6,
            "waiting": 0,
            "waitingPt": -2,
            "lateArrival": -18,
            "earlyDeparture": -0,
            "work": {
                "typicalDuration": "08:30:00",
                "openingTime": "06:00:00",
                "closingTime": "20:00:00",
                "latestStartTime": "09:30:00",
                "earliestEndTime": "16:00:00",
                "minimalDuration": "08:00:00",
            },
            "education": {
                "typicalDuration": "06:00:00",
                "openingTime": "06:00:00",
                "closingTime": "20:00:00",
                "minimalDuration": "01:00:00",
            },
            "home": {"typicalDuration": "12:00:00", "minimalDuration": "08:00:00"},
            "shop": {"typicalDuration": "00:30:00", "minimalDuration": "00:10:00"},
            "car": {
                "constant": -0,
                "dailyMonetaryConstant": -0,
                "dailyUtilityConstant": -0,
                "marginalUtilityOfDistance": -0,
                "marginalUtilityOfTravelling": -5,
                "monetaryDistanceRate": -0.0005,
            },
            "pt": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
            "bus": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
            "train": {"marginalUtilityOfTravelling": -5, "monetaryDistanceRate": -0.001},
            "walk": {"marginalUtilityOfTravelling": -12},
            "bike": {"marginalUtilityOfTravelling": -12},
        }
    }


@pytest.fixture
def config_complex():
    # londinium config
    return {
        "default": {
            "earlyDeparture": -0.0,
            "lateArrival": -18.0,
            "marginalUtilityOfMoney": 1.0,
            "performing": 6.0,
            "utilityOfLineSwitch": -1.0,
            "waiting": -0.0,
            "waitingPt": -2.0,
            "mUM": 1.0,
            "home": {
                "minimalDuration": "08:00:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "12:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "work": {
                "minimalDuration": "08:00:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "08:30:00",
                "typicalDurationScoreComputation": "relative",
            },
            "leisure": {
                "minimalDuration": "00:30:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "education": {
                "minimalDuration": "02:00:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "06:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "shop": {
                "minimalDuration": "00:15:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "medical": {
                "minimalDuration": "00:05:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "gym": {
                "minimalDuration": "00:30:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:30:00",
                "typicalDurationScoreComputation": "relative",
            },
            "park": {
                "minimalDuration": "00:30:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "pub": {
                "minimalDuration": "00:30:00",
                "priority": "1.0",
                "scoringThisActivityAtAll": "true",
                "typicalDuration": "01:00:00",
                "typicalDurationScoreComputation": "relative",
            },
            "car interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "pt interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "bus interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "rail interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "subway interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "ferry interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "access_walk interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "egress_walk interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "walk interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "bike interaction": {
                "priority": "1.0",
                "scoringThisActivityAtAll": "false",
                "typicalDurationScoreComputation": "relative",
            },
            "car": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.0005,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "pt": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "bus": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "rail": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "subway": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "ferry": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "access_walk": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "egress_walk": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "walk": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "bike": {
                "constant": 0.0,
                "dailyMonetaryConstant": 0.0,
                "dailyUtilityConstant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": -0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
        },
        "electric": {
            "lateArrival": -18.0,
            "earlyDeparture": -0.0,
            "marginalUtilityOfMoney": 1.0,
            "performing": 6.0,
            "waiting": -0.0,
            "waitingPt": -2.0,
            "utilityOfLineSwitch": -1.0,
            "mUM": 1.0,
            "home": {"priority": "1", "typicalDuration": "12:00:00", "minimalDuration": "08:00:00"},
            "work": {"priority": "1", "typicalDuration": "08:30:00", "minimalDuration": "08:00:00"},
            "education": {
                "priority": "1",
                "typicalDuration": "08:30:00",
                "minimalDuration": "06:00:00",
            },
            "shop": {"priority": "1", "typicalDuration": "00:30:00", "minimalDuration": "00:10:00"},
            "car": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.0005,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "pt": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "bus": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "train": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": 0.0,
                "marginalUtilityOfTraveling_util_hr": -5.0,
                "monetaryDistanceRate": -0.001,
                "marginalUtilityOfDistance": 0.0,
                "marginalUtilityOfTravelling": -5.0,
            },
            "access_walk": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "egress_walk": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "walk": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": 0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
            "bike": {
                "constant": 0.0,
                "marginalUtilityOfDistance_util_m": -0.0,
                "marginalUtilityOfTraveling_util_hr": -12.0,
                "monetaryDistanceRate": -0.0,
                "marginalUtilityOfDistance": -0.0,
                "marginalUtilityOfTravelling": -12.0,
            },
        },
    }


class FakeRoute:
    def __init__(self, btime=None):
        if btime is not None:
            self.transit = {"boardingTime": btime}
        else:
            self.transit = {}


@pytest.fixture()
def default_leg():
    default_leg = Leg(
        1,
        "walk",
        "a",
        "b",
        start_time=mtdt(8 * 60),
        end_time=mtdt(8 * 60 + 5),
        distance=5,
        route=FakeRoute(),
    )
    return default_leg


@pytest.fixture()
def pt_wait_leg():
    class FakeRoute:
        def __init__(self, btime):
            self.transit = {"boardingTime": btime}

    pt_wait_leg = Leg(
        1,
        "bus",
        "a",
        "b",
        start_time=mtdt(8 * 60),
        end_time=mtdt(8 * 60 + 15),
        distance=5,
        route=FakeRoute("08:05:00"),
    )
    return pt_wait_leg


@pytest.fixture()
def car_leg():
    car_leg = Leg(
        1, "car", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5), distance=5
    )
    return car_leg


@pytest.fixture()
def short_activity():
    short_activity = Activity(2, "work", "b", start_time=mtdt(8 * 60), end_time=mtdt(11 * 60))
    return short_activity


@pytest.fixture()
def late_activity():
    late_activity = Activity(2, "work", "b", start_time=mtdt(11 * 60), end_time=mtdt(18 * 60))
    return late_activity


@pytest.fixture()
def Anna():
    Anna = Person(
        4, attributes={"age": 6, "job": "education", "gender": "female", "subpopulation": "default"}
    )
    Anna.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Anna.add(
        Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30), distance=5)
    )
    Anna.add(Activity(2, "education", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Anna.add(
        Leg(2, "walk", "b", "c", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30), distance=5)
    )
    Anna.add(Activity(5, "home", "a", start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    return Anna


@pytest.fixture()
def AnnaPT():
    AnnaPT = Person(
        4, attributes={"age": 6, "job": "education", "gender": "female", "subpopulation": "default"}
    )
    AnnaPT.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    AnnaPT.add(
        Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 10), distance=1)
    )
    AnnaPT.add(
        Activity(1, "pt_interaction", "a", start_time=mtdt(8 * 60 + 10), end_time=mtdt(8 * 60 + 10))
    )
    AnnaPT.add(
        Leg(
            1, "bus", "a", "b", start_time=mtdt(8 * 60 + 10), end_time=mtdt(8 * 60 + 20), distance=5
        )
    )
    AnnaPT.add(
        Activity(1, "pt_interaction", "a", start_time=mtdt(8 * 60 + 20), end_time=mtdt(8 * 60 + 20))
    )
    AnnaPT.add(
        Leg(
            1, "bus", "a", "b", start_time=mtdt(8 * 60 + 20), end_time=mtdt(8 * 60 + 30), distance=5
        )
    )
    AnnaPT.add(
        Activity(1, "pt_interaction", "a", start_time=mtdt(8 * 60 + 30), end_time=mtdt(8 * 60 + 30))
    )
    AnnaPT.add(
        Leg(
            1,
            "walk",
            "a",
            "b",
            start_time=mtdt(8 * 60 + 30),
            end_time=mtdt(8 * 60 + 40),
            distance=1,
        )
    )
    AnnaPT.add(Activity(2, "education", "b", start_time=mtdt(8 * 60 + 40), end_time=mtdt(16 * 60)))
    AnnaPT.add(
        Leg(2, "walk", "b", "c", start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30), distance=5)
    )
    AnnaPT.add(Activity(5, "home", "a", start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    return AnnaPT


@pytest.fixture()
def early_activity():
    early_activity = Activity(2, "work", "b", start_time=mtdt(4 * 60), end_time=mtdt(11 * 60))
    return early_activity


@pytest.fixture()
def small_plan():
    Henry = Person(
        4,
        attributes={
            "age": 6,
            "job": "education",
            "gender": "male",
            "subpopulation": "subpopulation",
        },
    )
    Henry.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(24 * 60)))
    small_plan = Henry.plan
    return small_plan


@pytest.fixture()
def pt_person(test_trips_path):
    return read.read_matsim(test_trips_path, version=11)["census_1"]["census_1"]


@pytest.fixture()
def cyclist(test_trips_path):
    return read.read_matsim(test_trips_path)["census_2"]["census_2"]


@pytest.fixture
def population(test_trips_pathv12):
    return read.read_matsim(test_trips_pathv12, household_key="hid", weight=1, version=12)


@pytest.fixture(scope="module")
def population_no_args(test_trips_pathv12):
    return read.read_matsim(test_trips_pathv12, version=12)


@pytest.fixture
def population_experienced(test_experienced_pathv12):
    return read.read_matsim(test_experienced_pathv12, version=12)


@pytest.fixture
def data_zones():
    df = pd.DataFrame({"zone": ["a", "b"], "jobs": [100, 200], "schools": [3, 1]}).set_index("zone")
    return df


@pytest.fixture
def data_od():
    matrices = np.array(
        [[[[20, 30], [40, 45]], [[40, 45], [20, 30]]], [[[5, 5], [8, 9]], [[8, 9], [5, 5]]]]
    )
    return matrices


@pytest.fixture
def labels():
    labels = {
        "mode": ["car", "bus"],
        "vars": ["time", "distance"],
        "origin_zones": ["a", "b"],
        "destination_zones": ["a", "b"],
    }
    return labels


@pytest.fixture
def od(data_od, labels):
    od = OD(data=data_od, labels=labels)
    return od
