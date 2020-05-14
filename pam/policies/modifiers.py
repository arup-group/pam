import pam.core as core
import pam.activity as activity
from pam.policies import Policy
import random


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
        elif household is not None and isinstance(household, core.Household):
            self.remove_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. You need {} at the very least.'
                                      ''.format(type(household), type(person), type(activities), type(core.Household)))

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
        if household is not None and isinstance(household, core.Household):
            self.remove_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. This modifier exists only for Households'
                                      'you need to pass {}.'
                                      ''.format(type(household), type(person), type(activities), type(core.Household)))

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
            if isinstance(act, activity.Activity) and act in shared_activities_for_removal:
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
        elif household is not None and isinstance(household, core.Household):
            self.move_household_activities(household)
        else:
            raise NotImplementedError('Types passed incorrectly: {}, {}, {}. You need {} at the very least.'
                                      ''.format(type(household), type(person), type(activities), type(core.Household)))

    def move_activities(self, person, p):
        tours = self.matching_activity_tours(person.plan, p)
        if tours:
            for seq in range(len(person.plan)):
                if isinstance(person.plan[seq], activity.Activity):
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
        if set([act.act for act in tour]) - set(self.activities) == set():
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