from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional

import pam.activity
import pam.core


class Modifier(ABC):
    """Base class for modifiers - these are classes which change
    activities in a person's plan.

    In general a modifer should be able to be applied on three levels
    Household - apply change to all activities in all person's plans in household
    Person - apply change to all activities in a person's plan
    Activity - apply change to individual activity in a person's plan

    Not all modifiers will satisfy this of course, e.g. ReduceSharedActivity
    only works on a household level as the activites for removal need to be
    shared within a household.
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def apply_to(
        self,
        household: pam.core.Household,
        person: Optional[pam.core.Person] = None,
        activities: Optional[list[pam.activity.Activity]] = None,
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
        return "Modifier {} with attributes: {}".format(
            self.__class__.__name__, ", ".join("%s: %s" % item for item in attribs.items())
        )

    def print(self):
        print(self.__str__())


class RemoveActivity(Modifier):
    def __init__(self, activities: list[str]):
        """Removes specified activities.

        Args:
            activities (list[str]): List of activities to be removed.

        """
        super().__init__()
        self.activities = activities

    def apply_to(
        self,
        household: pam.core.Household,
        person: Optional[pam.core.Person] = None,
        activities: Optional[list[pam.activity.Activity]] = None,
    ) -> None:
        if activities and person:
            self.remove_individual_activities(person, activities)
        elif person:
            self.remove_person_activities(person)
        elif household and isinstance(household, pam.core.Household):
            self.remove_household_activities(household)
        else:
            raise TypeError(
                "Types passed incorrectly: {}, {}, {}. You need {} at the very least."
                "".format(type(household), type(person), type(activities), type(pam.core.Household))
            )

    def remove_activities(self, person, p):
        seq = 0
        while seq < len(person.plan):
            act = person.plan[seq]
            if self.is_activity_for_removal(act) and p(act):
                previous_idx, subsequent_idx = person.remove_activity(seq)
                person.fill_plan(previous_idx, subsequent_idx, default="home")
            else:
                seq += 1

    def remove_individual_activities(self, person, activities):
        def is_a_selected_activity(act):
            # more rigorous check if activity in activities; Activity.__eq__ is not sufficient here
            return act.isin_exact(activities)

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


class AddActivity(Modifier):
    def __init__(self, activities: list[str]):
        """Adds specified activities.

        Args:
            activities (list[str]): List of activities to be added.

        """
        super().__init__()
        self.activities = activities

    def apply_to(
        self,
        household: pam.core.Household,
        person: Optional[pam.core.Person] = None,
        activities: Optional[list[pam.activity.Activity]] = None,
    ) -> None:
        raise NotImplementedError("Watch this space")


class ReduceSharedActivity(Modifier):
    def __init__(self, activities: list[str]) -> None:
        """Policy that needs to be applied on a household level. For activities
        shared within a household (Activity.act (type of activity), start/end
        times and locations match). Randomly assigns a person whose activities
        will be retained and deletes the shared activities from other persons
        in household.

        Args:
            activities (list[str]):
                List of activities that should be considered for sharing.
                Does not require an exact match.
                E.g. if passed ['shop_food', 'shop_other'] if a household has an only 'shop_food' shared activity, that will be reduced.

        """
        super().__init__()
        self.activities = activities

    def apply_to(
        self,
        household: pam.core.Household,
        person: Optional[pam.core.Person] = None,
        activities: Optional[list[pam.activity.Activity]] = None,
    ) -> None:
        if household and isinstance(household, pam.core.Household):
            self.remove_household_activities(household)
        else:
            raise NotImplementedError(
                "Types passed incorrectly: {}, {}, {}. This modifier exists only for Households"
                "you need to pass {}."
                "".format(type(household), type(person), type(activities), type(pam.core.Household))
            )

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
            if isinstance(act, pam.activity.Activity) and act in shared_activities_for_removal:
                previous_idx, subsequent_idx = person.remove_activity(seq)
                person.fill_plan(previous_idx, subsequent_idx, default="home")
            else:
                seq += 1

    def remove_household_activities(self, household):
        acts_for_removal = self.shared_activities_for_removal(household)
        if acts_for_removal:
            # pick the person that retains activities
            ppl_sharing_activities = self.people_who_share_activities_for_removal(household)
            if ppl_sharing_activities:
                person_retaining_activities = random.choice(
                    self.people_who_share_activities_for_removal(household)
                )
                for pid, person in household.people.items():
                    if person != person_retaining_activities:
                        self.remove_activities(person, acts_for_removal)

    def is_activity_for_removal(self, p):
        return p.act.lower() in self.activities

    def shared_activities_for_removal(self, household):
        shared_activities = household.shared_activities()
        return [act for act in shared_activities if self.is_activity_for_removal(act)]

    def people_who_share_activities_for_removal(self, household):
        shared_activities_for_removal = self.shared_activities_for_removal(household)
        people_with_shared_acts_for_removal = []
        for pid, person in household.people.items():
            for activity in person.activities:
                if activity.isin_exact(shared_activities_for_removal):
                    people_with_shared_acts_for_removal.append(person)
        return people_with_shared_acts_for_removal


class MoveActivityTourToHomeLocation(Modifier):
    def __init__(self, activities: list[str], location: str = "home", new_mode: str = "walk"):
        """Moves a tour of activities to home location.

        A tour is defined as a list of activities sandwiched between two home activities.

        Args:
            activities:
                List of activities to be considered in a tour.
                Any combination of activities in activities sandwiched by home activities will be selected
                Does not require an exact match.
                E.g. if passed ['shop_food', 'shop_other'] if a person has a tour of only 'shop_food', the location of that activity will be changed.
            location (str): Location to which the tour should be moved. Defaults to "home".
            new_mode (str): Mode used in the legs to/from the activity when we relocate the activity. Defaults to "walk".

        """
        super().__init__()
        self.activities = activities
        self.default = location
        self.new_mode = new_mode

    def apply_to(
        self,
        household: pam.core.Household,
        person: Optional[pam.core.Person] = None,
        activities: Optional[list[pam.activity.Activity]] = None,
    ) -> None:
        new_mode = self.new_mode
        if activities and person:
            self.move_individual_activities(person, activities, new_mode)
        elif person:
            self.move_person_activities(person, new_mode)
        elif household and isinstance(household, pam.core.Household):
            self.move_household_activities(household, new_mode)
        else:
            raise NotImplementedError(
                "Types passed incorrectly: {}, {}, {}. You need {} at the very least."
                "".format(type(household), type(person), type(activities), type(pam.core.Household))
            )

    def move_activities(self, person, p, new_mode="walk"):
        tours = self.matching_activity_tours(person.plan, p)
        if tours:
            for seq in range(len(person.plan)):
                if isinstance(person.plan[seq], pam.activity.Activity):
                    act = person.plan[seq]
                    if self.is_part_of_tour(act, tours):
                        person.move_activity(seq, default=self.default, new_mode=new_mode)

    def move_individual_activities(self, person, activities, new_mode="walk"):
        def is_a_selected_activity(act):
            # more rigorous check if activity in activities; Activity.__eq__ is not sufficient here
            return act.isin_exact(activities)

        self.move_activities(person, p=is_a_selected_activity, new_mode=new_mode)

    def move_person_activities(self, person, new_mode="walk"):
        def return_true(act):
            return True

        self.move_activities(person, p=return_true, new_mode=new_mode)

    def move_household_activities(self, household, new_mode="walk"):
        for pid, person in household.people.items():
            self.move_person_activities(person, new_mode=new_mode)

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
            if act.isin_exact(tour):
                return True
        return False
