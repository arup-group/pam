from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt

import random


class Policy:

    def __init__(self):
        self.population = Population

    def apply_to(self, household):
        raise NotImplementedError


class HouseholdQuarantined(Policy):
    """
    Probabilistic everyone in household stays home

    by default, person_based=False: Probability household-based,
    i.e. the probability of a household being quarantined

    person_based=True: Probability person-based,
    i.e. the probability of any person in the household
    needing to be quarantined
    """

    def __init__(self, probability, person_based=False):
        super().__init__()

        assert 0 < probability <= 1
        self.probability = probability
        self.person_based = person_based

    def apply_to(self, household):
        if self.person_based:
            n = len(household.people)
            if random.random() < (1 - (1 - self.probability) ** n):
                for pid, person in household.people.items():
                    person.stay_at_home()
        else:
            if random.random() < self.probability:
                for pid, person in household.people.items():
                    person.stay_at_home()


class PersonStayAtHome(Policy):
    """
    Probabilistic person stays home
    """

    def __init__(self, probability):
        super().__init__()

        assert 0 < probability <= 1
        self.probability = probability

    def apply_to(self, household):
        for pid, person in household.people.items():
            if random.random() < self.probability:
                person.stay_at_home()


class RemoveActivity(Policy):
    """
    Probabilistic remove activities
    """

    def __init__(self, activities: list, probability):
        super().__init__()

        self.activities = activities
        assert 0 < probability <= 1
        self.probability = probability

    def apply_to(self, household):
        for pid, person in household.people.items():

            seq = 0
            while seq < len(person.plan):
                p = person.plan[seq]
                is_activity_for_removal = p.act.lower() in self.activities
                selected = random.random() < self.probability
                if is_activity_for_removal and selected:
                    previous_idx, subsequent_idx = person.remove_activity(seq)
                    person.fill_plan(previous_idx, subsequent_idx, default='home')
                else:
                    seq += 1


def apply_policies(population: Population, policies: list):

    """
    Apply policies to modify population.
    :param population:
    :param policies:
    :return:
    """

    for hid, household in population.households.items():
        for policy in policies:
            policy.apply_to(household)

