import random
from typing import Union
from copy import deepcopy
import pam.policy.modifiers as modifiers
import pam.policy.probability_samplers as probability_samplers
import pam.policy.filters as filters


class Policy:
    def __init__(self):
        pass

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))

    def __repr__(self):
        attribs = vars(self)
        return "<{} instance at {}: {}>".format(
            self.__class__.__name__,
            id(self),
            ', '.join("%r: %r" % item for item in attribs.items()))

    def __str__(self):
        attribs = vars(self)
        return  "Policy {} with attributes: \n{}".format(
            self.__class__.__name__,
            ', \n'.join("%s: %s" % item for item in attribs.items()))

    def print(self):
        print(self.__str__())


class PolicyLevel(Policy):
    def __init__(self, modifier: modifiers.Modifier, attribute_filter: filters.Filter = None):
        super().__init__()
        assert isinstance(modifier, modifiers.Modifier), 'modifier needs to be subclass of {}'.format(
            type(modifiers.Modifier()))
        self.modifier = modifier
        if attribute_filter is None:
            self.attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.attribute_filter = attribute_filter

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(PolicyLevel)))


class HouseholdPolicy(PolicyLevel):
    """
    Policy that needs to be applied on a household level

    if probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy

    """
    def __init__(self,
                 modifier: modifiers.Modifier,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(probability)

    def apply_to(self, household, person=None, activities=None):
        """
        uses self.probability to decide if household should be selected
        :param household:
        :param person:
        :param activities:
        :return:
        """
        if self.attribute_filter.satisfies_conditions(household):
            if isinstance(self.probability, list):
                p = 1
                for prob in self.probability:
                    p *= prob.p(household)
                if random.random() < p:
                    self.modifier.apply_to(household)
            elif self.probability.sample(household):
                self.modifier.apply_to(household)


class PersonPolicy(PolicyLevel):
    """
    Policy that needs to be applied on a person level
    """
    def __init__(self,
                 modifier: modifiers.Modifier,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability,
            (probability_samplers.HouseholdProbability))

    def apply_to(self, household, person=None, activities=None):
        for pid, person in household.people.items():
            if self.attribute_filter.satisfies_conditions(person):
                if isinstance(self.probability, list):
                    p = 1
                    for prob in self.probability:
                        p *= prob.p(person)
                    if random.random() < p:
                        self.modifier.apply_to(household, person)
                elif self.probability.sample(person):
                    self.modifier.apply_to(household, person)


class ActivityPolicy(PolicyLevel):
    """
    Policy that needs to be applied on an individual activity level
    """
    def __init__(self,
                 modifier: modifiers.Modifier,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability,
            (probability_samplers.HouseholdProbability, probability_samplers.PersonProbability))

    def apply_to(self, household, person=None, activities=None):
        for pid, person in household.people.items():
            if self.attribute_filter.satisfies_conditions(person):
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
                if activities_to_purge:
                    self.modifier.apply_to(household, person, activities_to_purge)


class HouseholdQuarantined(Policy):
    """
    Probabilistic everyone in household stays home
    """

    def __init__(self, probability):
        super().__init__()
        self.probability = probability_samplers.verify_probability(probability)

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
        self.probability = probability_samplers.verify_probability(probability)

    def apply_to(self, household, person=None, activity=None):
        for pid, person in household.people.items():
            if random.random() < self.probability.p(person):
                person.stay_at_home()


class RemoveHouseholdActivities(HouseholdPolicy):
    def __init__(self,
                 activities: list,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemovePersonActivities(PersonPolicy):
    def __init__(self,
                 activities: list,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemoveIndividualActivities(ActivityPolicy):
    def __init__(self,
                 activities: list,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class MovePersonActivitiesToHome(PersonPolicy):
    def __init__(self,
                 activities: list,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifiers.MoveActivityTourToHomeLocation(activities), probability, attribute_filter)


class ReduceSharedHouseholdActivities(HouseholdPolicy):
    def __init__(self,
                 activities: list,
                 probability: Union[float, int, probability_samplers.SamplingProbability],
                 attribute_filter: filters.Filter = None):
        super().__init__(modifiers.ReduceSharedActivity(activities), probability, attribute_filter)


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
