import random
import pam.policy.modifiers as modifiers
import pam.policy.probability_samplers as probability_samplers
import pam.policy.filters as filters
import pam.policy.policies as policies


class PolicyLevel(policies.Policy):
    def __init__(self):
        super().__init__()

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(PolicyLevel)))


class HouseholdPolicy(PolicyLevel):
    """
    Policy that needs to be applied on a household level

    if probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy

    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (modifiers.RemoveActivity, modifiers.AddActivity,
                                   modifiers.MoveActivityTourToHomeLocation, modifiers.ReduceSharedActivity))
        self.policy = policy
        self.probability = probability_samplers.verify_probability(
            probability,
            (float, list, probability_samplers.SimpleProbability, probability_samplers.ActivityProbability,
             probability_samplers.PersonProbability, probability_samplers.HouseholdProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.person_attribute_filter = person_attribute_filter

    def apply_to(self, household, person=None, activities=None):
        """
        uses self.probability to decide if household should be selected
        :param household:
        :param person:
        :param activities:
        :return:
        """
        if self.person_attribute_filter.satisfies_conditions(household):
            if isinstance(self.probability, list):
                p = 1
                for prob in self.probability:
                    p *= prob.p(household)
                if random.random() < p:
                    self.policy.apply_to(household)
            elif self.probability.sample(household):
                self.policy.apply_to(household)


class PersonPolicy(PolicyLevel):
    """
    Policy that needs to be applied on a person level
    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (modifiers.RemoveActivity, modifiers.AddActivity, modifiers.MoveActivityTourToHomeLocation))
        self.policy = policy
        self.probability = probability_samplers.verify_probability(
            probability,
            (float, list, probability_samplers.SimpleProbability, probability_samplers.ActivityProbability,
             probability_samplers.PersonProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.person_attribute_filter = person_attribute_filter

    def apply_to(self, household, person=None, activities=None):
        for pid, person in household.people.items():
            if self.person_attribute_filter.satisfies_conditions(person):
                if isinstance(self.probability, list):
                    p = 1
                    for prob in self.probability:
                        p *= prob.p(person)
                    if random.random() < p:
                        self.policy.apply_to(household, person)
                elif self.probability.sample(person):
                    self.policy.apply_to(household, person)


class ActivityPolicy(PolicyLevel):
    """
    Policy that needs to be applied on an individual activity level
    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (modifiers.RemoveActivity, modifiers.AddActivity,
                                   modifiers.MoveActivityTourToHomeLocation))
        self.policy = policy
        self.probability = probability_samplers.verify_probability(
            probability,
            (float, list, probability_samplers.SimpleProbability, probability_samplers.ActivityProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.person_attribute_filter = person_attribute_filter

    def apply_to(self, household, person=None, activities=None):
        for pid, person in household.people.items():
            if self.person_attribute_filter.satisfies_conditions(person):
                activities_to_purge = []
                for activity in person.activities:
                    if isinstance(self.probability, list):
                        p = 1
                        for prob in self.probability:
                            p *= prob.p(activity)
                        if random.random() < p:
                            activities_to_purge.append(activity)
                    elif self.probability.sample(activity):
                        activities_to_purge.append(activity)
                self.policy.apply_to(household, person, activities_to_purge)