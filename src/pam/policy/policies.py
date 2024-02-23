from __future__ import annotations

import random
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pam.activity import Activity
    from pam.core import Household, Person, Population

import pam.policy.filters as filters
import pam.policy.modifiers as modifiers
import pam.policy.probability_samplers as probability_samplers


class Policy(ABC):
    """Base class for policies."""

    def __init__(self):
        pass

    @abstractmethod
    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
        """Uses self.probability to decide if household/person/activity should be selected.

        Args:
            household (Household):
            person (Optional[Person], optional): Defaults to None.
            activities (Optional[list[Activity]], optional): Defaults to None.
        """

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

    def __init__(
        self, modifier: modifiers.Modifier, attribute_filter: Optional[filters.Filter] = None
    ):
        super().__init__()
        assert isinstance(
            modifier, modifiers.Modifier
        ), "modifier needs to be subclass of {}".format(type(modifiers.Modifier))
        self.modifier = modifier
        if attribute_filter is None:
            self.attribute_filter = filters.PersonAttributeFilter({})
        else:
            self.attribute_filter = attribute_filter

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
        super().apply_to(household, person, activities)


class HouseholdPolicy(PolicyLevel):
    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Policy that is to be applied on a household level.

        Args:
            modifier (modifiers.Modifier): The class which governs the change to be performed to the activities in a person's plan.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                A number or a subclass of the 'SamplingProbability' base class.
                The household policy accepts all levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Household.
            attribute_filter (filters.Filter, optional):
                If given, helps filter/select household for policy application based on object attributes. Defaults to None.
        """

        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(probability)

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
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
    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Policy that is to be applied on a person level.

        Args:
            modifier (modifiers.Modifier): the class which governs the change to be performed to the activities in a person's plan.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                A number or a subclass of the 'SamplingProbability' base class.
                The person policy accepts all but 'HouseholdProbability' level of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Person.
            attribute_filter (filters.Filter, optional):
                If given, helps filter/select person for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability, (probability_samplers.HouseholdProbability)
        )

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
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
    def __init__(
        self,
        modifier: modifiers.Modifier,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Policy that is to be applied on an individual activity level.

        Args:
            modifier (modifiers.Modifier): the class which governs the change to be performed to the activities in a person's plan.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                A number or a subclass of the 'SamplingProbability' base class.
                The activity policy accepts all but 'HouseholdProbability' and 'PersonProbability' levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Activity.
            attribute_filter (filters.Filter, optional):
                If given, helps filter/select activity for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifier, attribute_filter)
        self.probability = probability_samplers.verify_probability(
            probability,
            (probability_samplers.HouseholdProbability, probability_samplers.PersonProbability),
        )

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
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
    def __init__(
        self, probability: Union[float, int, probability_samplers.SamplingProbability]
    ) -> None:
        """Household level Policy which removes all non-home activities for all persons in a household.

        Args:
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                A number or a subclass of the 'SamplingProbability' base class.
                This policy accepts all levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Household.
        """
        super().__init__()
        self.probability = probability_samplers.verify_probability(probability)

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
        p = self.probability.p(household)
        if random.random() < p:
            for pid, person in household.people.items():
                person.stay_at_home()


class PersonStayAtHome(Policy):
    def __init__(
        self, probability: Union[float, int, probability_samplers.SamplingProbability]
    ) -> None:
        """Person level Policy which removes all non-home activities for a person.

        Args:
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                A number or a subclass of the 'SamplingProbability' base class.
                The person policy accepts all but 'HouseholdProbability' level of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Person.
        """
        super().__init__()
        self.probability = probability_samplers.verify_probability(
            probability, (probability_samplers.HouseholdProbability)
        )

    def apply_to(
        self,
        household: Household,
        person: Optional[Person] = None,
        activities: Optional[list[Activity]] = None,
    ) -> None:
        for pid, person in household.people.items():
            if random.random() < self.probability.p(person):
                person.stay_at_home()


class RemoveHouseholdActivities(HouseholdPolicy):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ):
        """Pre-packaged household-level policy which removes specified activities from all person's plans within selected households.

        Args:
            activities (list): List of activities to be removed.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                The household policy accepts all levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Household.
            attribute_filter (filters.Filter, optional):
                If given, helps filter/select household for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemovePersonActivities(PersonPolicy):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ):
        """Pre-packaged person-level policy which removes specified activities from all person's plans within selected households.

        Args:
            activities (list):  List of activities to be removed.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                The person policy accepts all levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Person.
            attribute_filter (filters.Filter, optional):
                If given, helps filter/select person for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class RemoveIndividualActivities(ActivityPolicy):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Pre-packaged activity-level policy which removes specified activities from all person's plans within selected households.

        Args:
            activities (list):  List of activities to be removed.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                The activity policy accepts all but 'HouseholdProbability' and 'PersonProbability' levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Activity.
            attribute_filter (Optional[filters.Filter], optional):
                If given, helps filter/select household for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifiers.RemoveActivity(activities), probability, attribute_filter)


class MovePersonActivitiesToHome(PersonPolicy):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Pre-packaged person-level policy which moves a tour of activities to home location.

        A tour is defined as a list of activities sandwiched between two home activities.

        Args:
            activities (list):
                List of activities to be considered in a tour.
                Does not require an exact match. E.g. if passed ['shop_food', 'shop_other'] if a person has a tour of only 'shop_food', the location of that activity will be changed.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                The activity policy accepts all but 'HouseholdProbability' level of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Person.
            attribute_filter (Optional[filters.Filter], optional):
                If given, helps filter/select household for policy application based on object attributes.. Defaults to None.
        """
        super().__init__(
            modifiers.MoveActivityTourToHomeLocation(activities), probability, attribute_filter
        )


class ReduceSharedHouseholdActivities(HouseholdPolicy):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, probability_samplers.SamplingProbability],
        attribute_filter: Optional[filters.Filter] = None,
    ) -> None:
        """Pre-packaged household-level policy which reduces the number of activities shared within a household.

        Activity.act (type of activity), start/end times and locations match.
        Randomly assigns a person whose activities will be retained and deletes the shared activities from other persons in household.

        Args:
            activities (list):
                List of activities that should be considered for sharing.
                Does not require an exact match. E.g. if passed ['shop_food', 'shop_other'] if a household has an only 'shop_food' shared activity, that will be reduced.
            probability (Union[float, int, probability_samplers.SamplingProbability]):
                The activity policy accepts all levels of Sampling Probabilities.
                If probability given as float: 0<probability<=1 then the probability level is assumed to be of the same level as the policy, i.e. Person.
            attribute_filter (Optional[filters.Filter], optional):
                If given, helps filter/select household for policy application based on object attributes. Defaults to None.
        """
        super().__init__(modifiers.ReduceSharedActivity(activities), probability, attribute_filter)


def apply_policies(
    population: Population, policies: Union[list[Policy], Policy], in_place: bool = False
) -> Optional[Population]:
    """Method which applies policies to population.

    Args:
      population (pam.core.Population):
      policies (Union[list[Policy], Policy]): Policies to be applied to the population.
      in_place (bool): Whether to apply policies to current Population (True) object or return a copy (False). Defaults to False.

    Returns:
      pam.core.Population, optional: if `in_place` is False.

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
