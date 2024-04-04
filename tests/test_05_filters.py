from random import choice

import pytest
from pam.activity import Activity
from pam.core import Household, Person
from pam.policy.filters import PersonAttributeFilter


def test_subclass_name_features_in_repr_string():
    attrib_filter = PersonAttributeFilter({})
    assert "{}".format(attrib_filter.__class__.__name__) in attrib_filter.__repr__()


def test_subclass_name_features_in_str_string():
    attrib_filter = PersonAttributeFilter({})
    assert "{}".format(attrib_filter.__class__.__name__) in attrib_filter.__str__()


def test_PersonAttributeFilter_satisfies_conditions_delegates_to_household_satisfies_conditions_when_given_household(
    mocker,
):
    mocker.patch.object(PersonAttributeFilter, "household_satisfies_conditions")

    hhld = Household(1)
    PersonAttributeFilter({}).satisfies_conditions(hhld)
    PersonAttributeFilter.household_satisfies_conditions.assert_called_once_with(hhld)


def test_PersonAttributeFilter_satisfies_conditions_delegates_to_person_satisfies_conditions_when_given_person(
    mocker,
):
    mocker.patch.object(PersonAttributeFilter, "person_satisfies_conditions")

    person = Person(1)
    PersonAttributeFilter({}).satisfies_conditions(person)
    PersonAttributeFilter.person_satisfies_conditions.assert_called_once_with(person)


def test_PersonAttributeFilter_satisfies_conditions_throws_exception_when_given_activity():
    with pytest.raises(NotImplementedError):
        PersonAttributeFilter({}).satisfies_conditions(Activity(1))


def test_PersonAttributeFilter_satisfies_conditions_throws_exception_when_given_whatever():
    with pytest.raises(NotImplementedError):
        PersonAttributeFilter({}).satisfies_conditions("whatever")


def test_PersonAttributeFilter_household_satisfies_conditions_when_conditions_empty():
    assert PersonAttributeFilter({}).satisfies_conditions(Household(1))


def test_PersonAttributeFilter_satisfies_conditions_when_one_person_satisfies_conditions(
    SmithHousehold,
):
    def equals_6(val):
        return val == 6

    conditions = {"age": equals_6}

    household = SmithHousehold

    people_satisfying_condition = 0
    for pid, person in household.people.items():
        people_satisfying_condition += equals_6(person.attributes["age"])
    assert people_satisfying_condition >= 1

    assert PersonAttributeFilter(conditions).household_satisfies_conditions(household)


def test_PersonAttributeFilter_household_does_not_satisfy_conditions_when_no_person_satisfies_conditions(
    SmithHousehold,
):
    def equals_0(val):
        return val == 0

    conditions = {"age": equals_0}

    household = SmithHousehold

    people_satisfying_condition = 0
    for pid, person in household.people.items():
        people_satisfying_condition += equals_0(person.attributes["age"])
    assert people_satisfying_condition == 0

    assert not PersonAttributeFilter(conditions).household_satisfies_conditions(household)


def test_PersonAttributeFilter_person_satisfies_conditions_returns_True_if_conditions_empty():
    assert PersonAttributeFilter({}).satisfies_conditions(Person(1))


def test_PersonAttributeFilter_person_satisfies_conditions_throws_exception_with_unknown_how():
    with pytest.raises(NotImplementedError) as e:
        PersonAttributeFilter(
            {"age": choice([True, False])}, how="?!?!"
        ).person_satisfies_conditions(Person(1))
    assert "?!?! not implemented, use only `all` or `any`" in str(e.value)
