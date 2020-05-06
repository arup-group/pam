from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt

import random


class PersonAttributeFilter:
    """
    Helps filtering Person attributes

    how='all' by default, means all conditions for a person need to be met
    how='any' means at least one condition needs to be met
    """
    def __init__(self, conditions, how='all'):
        self.conditions = conditions
        self.how = how

    def satisfies_conditions(self, x):
        if isinstance(x, Household):
            # household satisfies conditions if one person satisfies conditions according to self.how
            return self.household_satisfies_conditions(x)
        elif isinstance(x, Person):
            return self.person_satisfies_conditions(x)
        elif isinstance(x, Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def household_satisfies_conditions(self, household):
        if not self.conditions:
            return True
        for pid, person in household.people.items():
            if self.person_satisfies_conditions(person):
                return True
        return False

    def person_satisfies_conditions(self, person):
        if not self.conditions:
            return True
        elif self.how == 'all':
            satisfies_attribute_conditions = True
            for attribute_key, attribute_condition in self.conditions.items():
                satisfies_attribute_conditions &= attribute_condition(person.attributes[attribute_key])
            return satisfies_attribute_conditions
        elif self.how == 'any':
            satisfies_attribute_conditions = False
            for attribute_key, attribute_condition in self.conditions.items():
                satisfies_attribute_conditions |= attribute_condition(person.attributes[attribute_key])
            return satisfies_attribute_conditions
        else:
            raise NotImplementedError('{} not implemented, use only `all` or `any`'.format(self.how))


class Policy:
    def __init__(self):
        self.population = Population

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))


class HouseholdQuarantined(Policy):
    """
    Probabilistic everyone in household stays home
    """
    def __init__(self, probability):
        super().__init__()
        self.probability = verify_probability(
            probability,
            (float, list, SimpleProbability, ActivityProbability, PersonProbability, HouseholdProbability)
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


class RemoveActivity(Policy):
    """
    Probabilistic remove activities
    """
    def __init__(self, activities: list):
        super().__init__()
        self.activities = activities

    def apply_to(self, household, person=None, activities=None):
        if (activities is not None) and (person is not None):
            self.remove_individual_activities(person, activities)
        elif person is not None:
            self.remove_person_activities(person)
        elif household is not None and isinstance(household, Household):
            self.remove_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. You need {} at the very least.'
                                      ''.format(type(household), type(person), type(activities), type(Household)))

    def remove_activities(self, person, p):
        seq = 0
        while seq < len(person.plan):
            act = person.plan[seq]
            if self.is_activity_for_removal(act) and p(act):
                previous_idx, subsequent_idx = person.remove_activity(seq)
                person.fill_plan(previous_idx, subsequent_idx, default='home')
            else:
                seq += 1

    def remove_individual_activities(self, person, activities):
        def is_a_selected_activity(act):
            # more rigorous check if activity in activities; Activity.__eq__ is not sufficient here
            for other_act in activities:
                if act.is_exact(other_act):
                    return True
            return False
        self.remove_activities(person, p=is_a_selected_activity)

    def remove_person_activities(self, person):
        def return_true(act):
            return True
        self.remove_activities(person, p=return_true)

    def remove_household_activities(self, household):
        for pid, person in household.people.items():
            self.remove_person_activities(person)

    def is_activity_for_removal(self, p):
        return p.act.lower() in self.activities


class AddActivity(Policy):
    """
    Probabilistic add activities
    """
    def __init__(self, activities: list):
        super().__init__()
        self.activities = activities

    def apply_to(self, household, person=None, activities=None):
        raise NotImplementedError('Watch this space')


class MoveActivity(Policy):
    """
    Probabilistic move activities
    """
    def __init__(self, activities: list):
        super().__init__()
        self.activities = activities

    def apply_to(self, household, person=None, activities=None):
        raise NotImplementedError('Watch this space')


class HouseholdPolicy(Policy):
    """
    Policy that needs to be applied on a household level

    if probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy

    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivity))
        self.policy = policy
        self.probability = verify_probability(
            probability,
            (float, list, SimpleProbability, ActivityProbability, PersonProbability, HouseholdProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = PersonAttributeFilter({})
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


class PersonPolicy(Policy):
    """
    Policy that needs to be applied on a person level
    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivity))
        self.policy = policy
        self.probability = verify_probability(
            probability,
            (float, list, SimpleProbability, ActivityProbability, PersonProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = PersonAttributeFilter({})
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


class ActivityPolicy(Policy):
    """
    Policy that needs to be applied on an individual activity level
    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivity))
        self.policy = policy
        self.probability = verify_probability(
            probability,
            (float, list, SimpleProbability, ActivityProbability)
        )
        if person_attribute_filter is None:
            self.person_attribute_filter = PersonAttributeFilter({})
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


class SamplingProbability:
    def __init__(self):
        pass

    def sample(self, x):
        return random.random() < self.p(x)

    def p(self, x):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))


class SimpleProbability(SamplingProbability):
    def __init__(self, probability):
        super().__init__()
        assert 0 < probability <= 1
        self.probability = probability

    def p(self, x):
        return self.probability


class HouseholdProbability(SamplingProbability):
    def __init__(self, probability, kwargs=None):
        super().__init__()
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, Household):
            return self.compute_probability_for_household(x)
        elif isinstance(x, Person):
            raise NotImplementedError
        elif isinstance(x, Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def compute_probability_for_household(self, household):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(household, **self.kwargs)


class PersonProbability(SamplingProbability):
    def __init__(self, probability, kwargs=None):
        super().__init__()
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, Household):
            p = 1
            for pid, person in x.people.items():
                p *= 1 - self.compute_probability_for_person(person)
            return 1 - p
        elif isinstance(x, Person):
            return self.compute_probability_for_person(x)
        elif isinstance(x, Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def compute_probability_for_person(self, person):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(person, **self.kwargs)


class ActivityProbability(SamplingProbability):
    def __init__(self, activities : list, probability, kwargs=None):
        super().__init__()
        self.activities = activities
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, Household):
            p = 1
            for pid, person in x.people.items():
                for act in person.activities:
                    if self.is_relevant_activity(act):
                        p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, Person):
            p = 1
            for act in x.activities:
                if self.is_relevant_activity(act):
                    p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, Activity):
            if self.is_relevant_activity(x):
                return self.compute_probability_for_activity(x)
            return 0
        else:
            raise NotImplementedError

    def compute_probability_for_activity(self, activity):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(activity, **self.kwargs)

    def is_relevant_activity(self, act):
        return act.act.lower() in self.activities


def verify_probability(probability, acceptable_types):
    if isinstance(probability, int):
        probability = float(probability)
    assert isinstance(probability, acceptable_types)
    if isinstance(probability, float):
        assert 0 < probability <= 1
        probability = SimpleProbability(probability)
    elif isinstance(probability, list):
        for i in range(len(probability)):
            assert isinstance(
                probability[i], acceptable_types)
            if isinstance(probability[i], float):
                probability[i] = SimpleProbability(probability[i])
    return probability


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