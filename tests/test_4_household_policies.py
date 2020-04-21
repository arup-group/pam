from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam import modify

import pytest


@pytest.fixture
def population():

    population = Population()
    for hid in range(1, 11):
        household = Household(hid)
        for pid in range(2):
            pid = f"{hid}-{pid}"
            person = Person(pid)

            person.add(Activity(1, 'home', 'a'))
            person.add(Leg(1, 'car', 'a', 'b'))
            person.add(Activity(2, 'work', 'b'))
            person.add(Leg(2, 'car', 'b', 'a'))
            person.add(Activity(3, 'home', 'a'))

            household.add(person)
        population.add(household)

    for hid in range(10, 21):
        household = Household(hid)
        for pid in range(2):
            pid = f"{hid}-{pid}"
            person = Person(pid)

            person.add(Activity(1, 'home', 'a'))
            person.add(Leg(1, 'bus', 'a', 'b'))
            person.add(Activity(2, 'education', 'b'))
            person.add(Leg(2, 'bus', 'b', 'a'))
            person.add(Activity(3, 'home', 'a'))

            household.add(person)
        population.add(household)
    return population


def test_apply_full_hh_quarantine(population):
    policy = modify.HouseholdQuarantined(1)
    modify.apply_policies(population, [policy])
    assert len(population.households) == 20
    for hid, household in population.households.items():
        assert len(household.people) == 2
        for pid, person in household.people.items():
            assert len(person.plan) == 1
            assert isinstance(person.plan.day[0], Activity)


def test_apply_person_based_full_quarantine(population):
    policy = modify.HouseholdQuarantined(1, person_based=True)
    modify.apply_policies(population, [policy])
    assert len(population.households) == 20
    for hid, household in population.households.items():
        assert len(household.people) == 2
        for pid, person in household.people.items():
            assert len(person.plan) == 1
            assert isinstance(person.plan.day[0], Activity)


def test_apply_full_person_stay_at_home(population):
    policy = modify.PersonStayAtHome(1)
    modify.apply_policies(population, [policy])
    assert len(population.households) == 20
    for hid, household in population.households.items():
        assert len(household.people) == 2
        for pid, person in household.people.items():
            assert len(person.plan) == 1
            assert isinstance(person.plan.day[0], Activity)


def test_apply_two_policies(population):
    policy1 = modify.HouseholdQuarantined(.1)
    policy2 = modify.PersonStayAtHome(.4)
    counter = 0
    modify.apply_policies(population, [policy1, policy2])
    assert len(population.households) == 20
    for hid, household in population.households.items():
        assert len(household.people) == 2
        for pid, person in household.people.items():
            counter += len(person.plan) == 1
    assert counter < 60  # super dodgy test with probability
