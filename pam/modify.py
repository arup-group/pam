from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt

import random


class Filter:
    def __init__(self):
        pass

    def satisfies_conditions(self, x):
        pass


class PersonAttributeFilter(Filter):
    """
    Helps filtering Person attributes

    how='all' by default, means all conditions for a person need to be met
    how='any' means at least one condition needs to be met
    """
    def __init__(self, conditions, how='all'):
        super().__init__()
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
            return act.in_list_exact(activities)
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


class ReduceSharedActivity(Policy):
    """
    Policy that needs to be applied on an individual activity level
    for activities that are shared  within the  household
    """
    def __init__(self, activities: list):
        super().__init__()
        self.activities = activities

    def apply_to(self, household, person=None, activities=None):
        if household is not None and isinstance(household, Household):
            self.remove_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. This modifier exists only for Households'
                                      'you need to pass {}.'
                                      ''.format(type(household), type(person), type(activities), type(Household)))

    def remove_activities(self, person, shared_activities_for_removal):
        seq = 0
        while seq < len(person.plan):
            act = person.plan[seq]
            # TODO there is a bug here `act in shared_activities_for_removal` should really be
            # act.in_list_exact(shared_activities_for_removal), but if tthere is more than one
            # activity in shared_activities_for_removal and  the  activities adjoin the
            # activities morph and change time, making them not satisfy self.is_exact(other) anymore
            # in this implementation however, you risk deleting isolated activities that have the
            # same name and location but aren't shared
            if isinstance(act, Activity) and act in shared_activities_for_removal:
                previous_idx, subsequent_idx = person.remove_activity(seq)
                person.fill_plan(previous_idx, subsequent_idx, default='home')
            else:
                seq += 1

    def remove_household_activities(self, household):
        acts_for_removal = self.shared_activities_for_removal(household)
        if acts_for_removal:
            # pick the person that retains activities
            ppl_sharing_activities = self.people_who_share_activities_for_removal(household)
            if ppl_sharing_activities:
                person_retaining_activities = random.choice(self.people_who_share_activities_for_removal(household))
                for pid, person in household.people.items():
                    if person != person_retaining_activities:
                        self.remove_activities(person, acts_for_removal)

    def is_activity_for_removal(self, p):
        return p.act.lower() in self.activities

    def shared_activities_for_removal(self, household):
        shared_activities = household.shared_activities()
        shared_activities_for_removal = []
        for act in shared_activities:
            if self.is_activity_for_removal(act):
                shared_activities_for_removal.append(act)
        return shared_activities_for_removal

    def people_who_share_activities_for_removal(self, household):
        shared_activities_for_removal = self.shared_activities_for_removal(household)
        people_with_shared_acts_for_removal = []
        for pid, person in household.people.items():
            for activity in person.activities:
                if activity.in_list_exact(shared_activities_for_removal):
                    people_with_shared_acts_for_removal.append(person)
        return people_with_shared_acts_for_removal


class MoveActivityTourToHomeLocation(Policy):
    """
    Probabilistic move chain of activities
    """
    def __init__(self, activities: list, default='home'):
        super().__init__()
        # list of activities defines the accepted activity tour,
        # any combination of activities in activities sandwiched
        # by home activities will be selected
        self.activities = activities
        self.default = default

    def apply_to(self, household, person=None, activities=None):
        if (activities is not None) and (person is not None):
            self.move_individual_activities(person, activities)
        elif person is not None:
            self.move_person_activities(person)
        elif household is not None and isinstance(household, Household):
            self.move_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. You need {} at the very least.'
                                      ''.format(type(household), type(person), type(activities), type(Household)))

    def move_activities(self, person, p):
        tours = self.matching_activity_tours(person.plan, p)
        if tours:
            for seq in range(len(person.plan)):
                if isinstance(person.plan[seq], Activity):
                    act = person.plan[seq]
                    if self.is_part_of_tour(act, tours):
                        person.move_activity(seq, default=self.default)

    def move_individual_activities(self, person, activities):
        def is_a_selected_activity(act):
            # more rigorous check if activity in activities; Activity.__eq__ is not sufficient here
            return act.in_list_exact(activities)
        self.move_activities(person, p=is_a_selected_activity)

    def move_person_activities(self, person):
        def return_true(act):
            return True
        self.move_activities(person, p=return_true)

    def move_household_activities(self, household):
        for pid, person in household.people.items():
            self.move_person_activities(person)

    def matching_activity_tours(self, plan, p):
        tours = plan.activity_tours()
        matching_tours = []
        for tour in tours:
            if self.tour_matches_activities(tour, p):
                matching_tours.append(tour)
        return matching_tours

    def tour_matches_activities(self, tour, p):
        if set([act.act for act in tour]) == set(self.activities):
            for act in tour:
                if p(act):
                    return True
        return False

    def is_part_of_tour(self, act, tours: list):
        for tour in tours:
            # more rigorous check if activity in activities; Activity.__eq__ is not sufficient here
            if act.in_list_exact(tour):
                return True
        return False


class HouseholdPolicy(Policy):
    """
    Policy that needs to be applied on a household level

    if probability given as float: 0<probability<=1 then the probability
    level is assumed to be of the same level as the policy

    """
    def __init__(self, policy, probability, person_attribute_filter=None):
        super().__init__()
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivityTourToHomeLocation, ReduceSharedActivity))
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
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivityTourToHomeLocation))
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
        assert isinstance(policy, (RemoveActivity, AddActivity, MoveActivityTourToHomeLocation))
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