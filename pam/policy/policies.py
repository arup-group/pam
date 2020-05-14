import pam.policy.probability_samplers as probability_samplers
import random


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
        self.probability = probability_samplers.verify_probability(
            probability,
            (float, list, probability_samplers.SimpleProbability, probability_samplers.ActivityProbability,
             probability_samplers.PersonProbability, probability_samplers.HouseholdProbability)
        )

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
