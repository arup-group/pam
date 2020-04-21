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

    attribute_conditions = {'attribute_key': attribute_condition},
    where attribute_condition:

    def attribute_condition(attribute_value):
        return boolean

    e.g.
    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    and
    attribute_conditions = {'age': age_condition_over_17}

    strict_conditions=True: person needs to satisfy
    all conditions in attribute_conditions
    strict_conditions=False: person needs to satisfy
    just one condition in attribute_conditions
    """

    def __init__(self, activities: list, probability, attribute_conditions=None, strict_conditions=True):
        super().__init__()

        self.activities = activities
        assert 0 < probability <= 1
        self.probability = probability
        assert attribute_conditions != {}, 'attribute_conditions cannot be empty'
        self.attribute_conditions = attribute_conditions
        assert isinstance(strict_conditions, bool)
        self.strict_conditions = strict_conditions

    def apply_to(self, household):
        for pid, person in household.people.items():

            if self.attribute_conditions is not None:
                if self.strict_conditions:
                    satisfies_attribute_conditions = True
                    for attribute_key, attribute_condition in self.attribute_conditions.items():
                        satisfies_attribute_conditions &= attribute_condition(person.attributes[attribute_key])
                else:
                    satisfies_attribute_conditions = False
                    for attribute_key, attribute_condition in self.attribute_conditions.items():
                        satisfies_attribute_conditions |= attribute_condition(person.attributes[attribute_key])

                if satisfies_attribute_conditions:
                    self.remove_activities(person)
            else:
                self.remove_activities(person)

    def remove_activities(self, person):
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

