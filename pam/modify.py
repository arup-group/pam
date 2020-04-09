from .core import Population, Household, Person, Activity, Leg, minutes_to_datetime

import random


class Policy:

    def __init__(self):
        self.population = Population

    def apply_to(self, household):
        raise NotImplementedError


class HouseholdQuarantined(Policy):
    """
    Probabilistic everyone in household stays home
    """

    def __init__(self, probability):
        super().__init__()

        assert 0 < probability <= 1
        self.probability = probability

    def apply_to(self, household):
        if random.random() < self.probability:
            for pid, person in household.people.items():
                person.plan = []
                person.add(
                    Activity(
                        1,
                        'home',
                        household.area,
                        start_time=minutes_to_datetime(0),
                        end_time=minutes_to_datetime(24*60-1)
                    )
                )


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
                person.plan = []
                person.add(
                    Activity(
                        1,
                        'home',
                        household.area,
                        start_time=minutes_to_datetime(0),
                        end_time=minutes_to_datetime(24 * 60 - 1)
                    )
                )


class RemoveActivity(Policy):
    """
    Probabilistic remove activities
    """

    def __init__(self, activities: str, probability):
        super().__init__()

        self.activities = activities
        assert 0 < probability <= 1
        self.probability = probability

    def apply_to(self, household):
        for pid, person in household.people.items():

            seq = 0
            while seq < len(person.plan):
                p = person.plan[seq]
                is_education = p.act.lower() in self.activities
                selected = random.random() < self.probability
                if is_education and selected:
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

