import random
from copy import deepcopy
from typing import List, Union

import pam.policy.filters as filters
import pam.policy.modifiers as modifiers
import pam.policy.probability_samplers as probability_samplers


class Policy:
    """Base class for policies."""

    def __init__(self):
        pass

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError("{} is a base class".format(type(Policy)))

    def __repr__(self):
        attribs = vars(self)
        return "<{} instance at {}: {}>".format(
            self.__class__.__name__,
            id(self),
            ", ".join("%r: %r" % item for item in attribs.items()),
        )

    def __str__(self):
        attribs = vars(self)
        return "Policy {} with attributes: \n{}".format(
            self.__class__.__name__, ", \n".join("%s: %s" % item for item in attribs.items())
        )

    def print(self):
        print(self.__str__())


class PolicyLevel(Policy):
    """Base class to formalise the hierarchy of levels at which a policy should applied at."""

    def __init__(self, modifier: modifiers.Modifier, attribute_filter: filters.Filter = None):
        super().__init__()
        assert isinstance(
            modifier, modifiers.Modifier
        ), "modifier needs to be subclass of {}".format(type(modifiers.Modifier()))
        self.modifier = modifier
        if attribute_filter is None:
            self.attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.attribute_filter = attribute_filter

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError("{} is a base class".format(type(PolicyLevel)))


class HouseholdPolicy(PolicyLevel):
    """Policy that is to be applied on a household level.

    Parameters
    ----------
    :param modifier
    A subclass of the 'Modifier' base class - the class which
    governs the change to be performed to the activities
    in a person's plan.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The household policy accepts all levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Household.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(probability)

    def apply_to(self, household, person=None, activities=None):
        """Uses self.probability to decide if household should be selected
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
    """Policy that is to be applied on a person level.

    Parameters
    ----------
    :param modifier
    A subclass of the 'Modifier' base class - the class which
    governs the change to be performed to the activities
    in a person's plan.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The person policy accepts all but 'HouseholdProbability' level
    of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Person.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select person for policy application
    based on object attributes.
    """

    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability, (probability_samplers.HouseholdProbability)
        )

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
    """Policy that is to be applied on an individual activity level.

    Parameters
    ----------
    :param modifier
    A subclass of the 'Modifier' base class - the class which
    governs the change to be performed to the activities
    in a person's plan.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The activity policy accepts all but 'HouseholdProbability' and
    'PersonProbability' levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Activity.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select activity for policy application
    based on object attributes.
    """

    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability,
            (probability_samplers.HouseholdProbability, probability_samplers.PersonProbability),
        )

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
    """Household level Policy which removes all non-home activities
    for all persons in a household.

    Parameters
    ----------
    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    This policy accepts all levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Household.
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
    """Person level Policy which removes all non-home activities
    for a person.

    Parameters
    ----------
    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The person policy accepts all but 'HouseholdProbability' level
    of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Person.
    """

    def __init__(self, probability):
        super().__init__()
        self.probability = probability_samplers.verify_probability(
            probability, (probability_samplers.HouseholdProbability)
        )

    def apply_to(self, household, person=None, activity=None):
        for pid, person in household.people.items():
            if random.random() < self.probability.p(person):
                person.stay_at_home()


class RemoveHouseholdActivities(HouseholdPolicy):
    """Pre-packaged household-level policy which removes specified
    activities from all person's plans within selected households.

    Parameters
    ----------
    :param activities
    List of activities to be removed.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The household policy accepts all levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Household.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemovePersonActivities(PersonPolicy):
    """Pre-packaged person-level policy which removes specified
    activities from all person's plans within selected households.

    Parameters
    ----------
    :param activities
    List of activities to be removed.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The person policy accepts all but 'HouseholdProbability' level
    of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Person.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemoveIndividualActivities(ActivityPolicy):
    """Pre-packaged activity-level policy which removes specified
    activities from all person's plans within selected households.

    Parameters
    ----------
    :param activities
    List of activities to be removed.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The activity policy accepts all but 'HouseholdProbability' and
    'PersonProbability' levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Activity.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class MovePersonActivitiesToHome(PersonPolicy):
    """Pre-packaged person-level policy which moves a tour of activities
    to home location. A tour is defined as a list of activities sandwiched
    between two home activities.

    Parameters
    ----------
    :param activities
    List of activities to be considered in a tour. Does not
    require an exact match. E.g. if passed ['shop_food', 'shop_other']
    if a person has a tour of only 'shop_food', the location of that
    activity will be changed.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The activity policy accepts all but 'HouseholdProbability' level
    of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Person.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(
            modifiers.MoveActivityTourToHomeLocation(activities), probability, attribute_filter
        )


class ReduceSharedHouseholdActivities(HouseholdPolicy):
    """Pre-packaged household-level policy which reduces the number of activities
    shared within a household (Activity.act (type of activity), start/end
    times and locations match). Randomly assigns a person whose activities
    will be retained and deletes the shared activities from other persons
    in household.

    Parameters
    ----------
    :param activities
    List of activities that should be considered for sharing. Does not
    require an exact match. E.g. if passed ['shop_food', 'shop_other']
    if a household has an only 'shop_food' shared activity, that will
    be reduced.

    :param probability
    A number or a subclass of the 'SamplingProbability' base class.
    The activity policy accepts all levels of Sampling Probabilities.
    If probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy, i.e. Person.

    :param attribute_filter, default 'None'
    Optional argument which helps filter/select household for policy application
    based on object attributes.
    """

    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: filters.Filter = None,
    ):
        super().__init__(modifiers.ReduceSharedActivity(activities), probability, attribute_filter)


def apply_policies(population, policies: Union[List[Policy], Policy], in_place=False):
    """Method which applies policies to population.

    Parameters
    ----------
    :param population:
    pam.core.Population object

    :param policies:
    A single instance of a sublass of pam.policy.policies.Policy subclasses
    or a list of them. Policies to be applied to the population.

    :param in_place: {'True', 'False'}, default 'False'
    Whether to apply policies to current Population object
    or return a copy.

    * True: applies policies to current Population object
    * False: applies policies to a copy of the passed Population object
    :return: pam.core.Population if in_place=='False'
    """
    if not in_place:
        pop = deepcopy(population)
    else:
        pop = population

    if isinstance(policies, Policy):
        policies = [policies]
    for i in range(len(policies)):
        policy = policies[i]
        assert isinstance(
            policy, Policy
        ), "Policies need to be of type {}, not {}. Failed for policy {} at list index {}".format(
            type(Policy), type(policy), policy, i
        )
    for hid, household in pop.households.items():
        for policy in policies:
            policy.apply_to(household)
    if not in_place:
        return pop
