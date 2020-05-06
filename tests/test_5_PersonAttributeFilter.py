from pam import modify
from pam.core import Household, Person
from pam.activity import Plan, Activity, Leg
import pytest
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from random import choice


def instantiate_household_with(persons: list):
    household = Household(1)
    for person in persons:
        household.add(person)
    return household


@pytest.fixture()
def Steve():
    Steve = Person('Steve', attributes={'age': 50, 'job': 'work', 'gender': 'male'})
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
    Hilda = Person('Hilda', attributes={'age': 45, 'job': 'influencer', 'gender': 'female'})
    Hilda.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Leg(1, 'pt', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, 'shop', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Hilda.add(Leg(2, 'pt', 'b', 'c', start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Hilda.add(Activity(3, 'leisure', 'c', start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20)))
    Hilda.add(Leg(3, 'pt', 'c', 'b', start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    return Hilda


@pytest.fixture()
def Timmy():
    Timmy = Person('Timmy', attributes={'age': 18, 'job': 'education', 'gender': 'male'})
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
    Bobby = Person('Bobby', attributes={'age': 6, 'job': 'education', 'gender': 'non-binary'})
    Bobby.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobby.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobby.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobby.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobby.add(Activity(5, 'home', 'a', start_time=mtdt(18 * 60 + 30), end_time=END_OF_DAY))
    return Bobby


@pytest.fixture()
def Smith_Household(Steve, Hilda, Timmy, Bobby):
    return instantiate_household_with([Steve, Hilda, Timmy, Bobby])


def test_PersonAttributeFilter_satisfies_conditions_delegates_to_household_satisfies_conditions_when_given_household(mocker):
    mocker.patch.object(modify.PersonAttributeFilter, 'household_satisfies_conditions')

    hhld = Household(1)
    modify.PersonAttributeFilter({}).satisfies_conditions(hhld)
    modify.PersonAttributeFilter.household_satisfies_conditions.assert_called_once_with(hhld)


def test_PersonAttributeFilter_satisfies_conditions_delegates_to_person_satisfies_conditions_when_given_person(mocker):
    mocker.patch.object(modify.PersonAttributeFilter, 'person_satisfies_conditions')

    person = Person(1)
    modify.PersonAttributeFilter({}).satisfies_conditions(person)
    modify.PersonAttributeFilter.person_satisfies_conditions.assert_called_once_with(person)


def test_PersonAttributeFilter_satisfies_conditions_throws_exception_when_given_activity():
    with pytest.raises(NotImplementedError) as e:
        modify.PersonAttributeFilter({}).satisfies_conditions(Activity(1))


def test_PersonAttributeFilter_satisfies_conditions_throws_exception_when_given_whatever():
    with pytest.raises(NotImplementedError) as e:
        modify.PersonAttributeFilter({}).satisfies_conditions('whatever')


def test_PersonAttributeFilter_household_satisfies_conditions_returns_True_if_conditions_empty():
    assert modify.PersonAttributeFilter({}).satisfies_conditions(Household(1))


def test_PersonAttributeFilter_household_satisfies_conditions_returns_True_if_one_person_satisfies_conditions(Smith_Household):
    def condition_age_6(val):
        return val == 6
    conditions = {'age': condition_age_6}

    household = Smith_Household

    people_satisfying_age_condition_equal_6 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_equal_6 += condition_age_6(person.attributes['age'])
    assert people_satisfying_age_condition_equal_6 >= 1

    assert modify.PersonAttributeFilter(conditions).household_satisfies_conditions(household)


def test_PersonAttributeFilter_household_satisfies_conditions_returns_False_if_no_person_satisfies_conditions(Smith_Household):
    def condition_age_0(val):
        return val == 0
    conditions = {'age': condition_age_0}

    household = Smith_Household

    people_satisfying_age_condition_equal_6 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_equal_6 += condition_age_0(person.attributes['age'])
    assert people_satisfying_age_condition_equal_6 == 0

    assert not modify.PersonAttributeFilter(conditions).household_satisfies_conditions(household)


def test_PersonAttributeFilter_person_satisfies_conditions_returns_True_if_conditions_empty():
    assert modify.PersonAttributeFilter({}).satisfies_conditions(Person(1))


def test_PersonAttributeFilter_person_satisfies_conditions_throws_exception_with_unknown_how():
    with pytest.raises(NotImplementedError) as e:
        modify.PersonAttributeFilter({'age': choice([True, False])}, how='?!?!').person_satisfies_conditions(Person(1))
    assert '?!?! not implemented, use only `all` or `any`' in str(e.value)
