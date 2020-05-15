import pam.policy.probability_samplers
import random
from copy import deepcopy
from typing import Union


class Policy:
    def __init__(self):
        pass

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))


class HouseholdQuarantined(Policy):
    """
    Probabilistic everyone in household stays home
    """
    def __init__(self, probability):
        super().__init__()
        self.probability = pam.policy.probability_samplers.verify_probability(probability)

    def apply_to(self, household, person=None, activity=None):
        p = self.probability.p(household)
        if random.random() < p:
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

    def apply_to(self, household, person=None, activity=None):
        for pid, person in household.people.items():
            if random.random() < self.probability:
                person.stay_at_home()


def apply_policies(population, policies: Union[list, Policy], in_place=False):
    if not in_place:
        pop = deepcopy(population)
    else:
        pop = population

    if isinstance(policies, Policy):
        policies = [policies]
    for i in range(len(policies)):
        policy = policies[i]
        assert isinstance(policy, Policy), \
            'Policies need to be of type {}, not {}. Failed for policy {} at list index {}'.format(
                type(Policy), type(policy), policy, i)
    for hid, household in pop.households.items():
        for policy in policies:
            policy.apply_to(household)
    if not in_place:
        return pop
