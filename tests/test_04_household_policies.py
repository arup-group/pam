import pytest
from pam.activity import Activity, Leg
from pam.core import Household, Person, Population
from pam.policy import policies, probability_samplers
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def assert_single_home_activity(person):
    assert len(person.plan) == 1
    assert isinstance(person.plan.day[0], Activity)
    assert person.plan.day[0].act == "home"
    assert person.plan.day[0].location == person.home
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[0].end_time == END_OF_DAY


@pytest.fixture
def population():
    population = Population()
    for hid in range(1, 11):
        household = Household(hid)
        for pid in range(2):
            pid = f"{hid}-{pid}"
            person = Person(pid)

            person.add(Activity(1, "home", "a"))
            person.add(Leg(1, "car", "a", "b"))
            person.add(Activity(2, "work", "b"))
            person.add(Leg(2, "car", "b", "a"))
            person.add(Activity(3, "home", "a"))

            household.add(person)
        population.add(household)

    for hid in range(10, 21):
        household = Household(hid)
        for pid in range(2):
            pid = f"{hid}-{pid}"
            person = Person(pid)

            person.add(Activity(1, "home", "a"))
            person.add(Leg(1, "bus", "a", "b"))
            person.add(Activity(2, "education", "b"))
            person.add(Leg(2, "bus", "b", "a"))
            person.add(Activity(3, "home", "a"))

            household.add(person)
        population.add(household)
    return population


def test_apply_full_hh_quarantine_doesnt_create_or_delete_households(population):
    policy = policies.HouseholdQuarantined(1)
    policies.apply_policies(population, policy, in_place=True)
    assert len(population.households) == 20


def test_apply_person_based_full_hh_quarantine_doesnt_create_or_delete_households(population):
    policy = policies.HouseholdQuarantined(probability_samplers.PersonProbability(1))
    policies.apply_policies(population, policy, in_place=True)
    assert len(population.households) == 20


def test_apply_full_hh_quarantine(population):
    policy = policies.HouseholdQuarantined(1)
    policies.apply_policies(population, policy, in_place=True)
    for hid, household in population.households.items():
        for pid, person in household.people.items():
            assert_single_home_activity(person)


def test_apply_person_based_full_quarantine(population):
    policy = policies.HouseholdQuarantined(probability_samplers.PersonProbability(1))
    policies.apply_policies(population, policy, in_place=True)
    for hid, household in population.households.items():
        for pid, person in household.people.items():
            assert_single_home_activity(person)


def test_apply_full_person_stay_at_home(population):
    policy = policies.PersonStayAtHome(1)
    policies.apply_policies(population, policy, in_place=True)
    for hid, household in population.households.items():
        for pid, person in household.people.items():
            assert_single_home_activity(person)


def test_apply_two_policies(population):
    policy1 = policies.HouseholdQuarantined(0.1)
    policy2 = policies.PersonStayAtHome(0.4)
    counter = 0
    policies.apply_policies(population, [policy1, policy2], in_place=True)
    for hid, household in population.households.items():
        assert len(household.people) == 2
        for pid, person in household.people.items():
            counter += len(person.plan) == 1
    assert counter < 60  # super dodgy test with probability
