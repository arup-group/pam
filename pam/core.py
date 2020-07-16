import logging
import random
import pickle

import pam.activity as activity
import pam.plot as plot
from pam import write
from pam import PAMSequenceValidationError, PAMTimesValidationError, PAMValidationLocationsError


class Population:

    def __init__(self, name=None):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.households = {}

    def add(self, household):
        if not isinstance(household, Household):
            raise UserWarning(f"Expected instance of Household, not: {type(household)}")
        self.households[str(household.hid)] = household

    def get(self, hid, default=None):
        return self.households.get(hid, default)

    def __getitem__(self, hid):
        return self.households[hid]

    def __iter__(self):
        for hid, household in self.households.items():
            yield hid, household

    def people(self):
        """
        Iterator for people in poulation, returns hid, pid and Person
        """
        for hid, household in self.households.items():
            for pid, person in household.people.items():
                yield hid, pid, person

    @property
    def population(self):
        return len([1 for hid, pid, person in self.people()])

    @property
    def num_households(self):
        return len([1 for hid, hh in self.households.items()])

    @property
    def size(self):
        return sum([person.freq for _, _, person in self.people()])

    @property
    def activity_classes(self):
        acts = set()
        for _, _, p in self.people():
            acts.update(p.activity_classes)
        return acts

    @property
    def mode_classes(self):
        modes = set()
        for _, _, p in self.people():
            modes.update(p.mode_classes)
        return modes

    def random_household(self):
        return self.households[random.choice(list(self.households))]

    def random_person(self):
        hh = self.random_household()
        return hh.random_person()

    @property
    def stats(self):
        num_households = 0
        num_people = 0
        num_activities = 0
        num_legs = 0
        for hid, household in self:
            num_households += 1
            for pid, person in household:
                num_people += 1
                num_activities += person.num_activities
                num_legs += person.num_legs
        return {
            'num_households': num_households,
            'num_people': num_people,
            'num_activities': num_activities,
            'num_legs': num_legs,
        }

    def fix_plans(self, crop=True, times=True, locations=True):
        for _, _, person in self.people():
            if crop:
                person.plan.crop()
            if times:
                person.plan.fix_time_consistency()
            if locations:
                person.plan.fix_location_consistency()

    def print(self):
        print(self)
        for _, household in self:
            household.print()

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)

    def to_csv(self, dir, crs=None, to_crs="EPSG:4326"):
        write.to_csv(self, dir, crs, to_crs)

    def __str__(self):
        return f"Population: {self.population} people in {self.num_households} households."

    def sample_locs2(self, sampler):
        """
        WIP Sample plan locs using a sampler
        TODO - add method to all core classes
        TODO - home location consistency within household
        """

        for _, _, person in self.people():
            uniques = {}
            for act in person.activities:
                if (act.location.area, act.act) in uniques:
                    loc = uniques[(act.location.area, act.act)]
                    act.location.loc = loc
                        
                else:
                    loc = sampler.sample(act.location.area, act.act)
                    uniques[(act.location.area, act.act)] = loc
                    act.location.loc = loc
            for idx in range(person.plan.length):
                component = person.plan[idx]
                if isinstance(component, activity.Leg):
                    component.start_location.loc = person.plan[idx-1].location.loc
                    component.end_location.loc = person.plan[idx+1].location.loc

    def sample_locs(self, sampler):
        """
        WIP Sample household plan locs using a sampler.

        Sampler uses activity types and areas to sample locations. Note that households share
        locations for activities of the same type within the same area. Trivially this includes
        household location. But also, for example, shopping activities if they are in the same area.

        We treat escort activities (ie those prefixed by "escort_") as the escorted activity. For
        example, the sampler treats "escort_education" and "education" equally. Note that this shared
        activity sampling of location models shared facilities, but does not explicitly infer or
        model shared transport. For example there is no consideration of if trips to shared locations
        take place at the same time or from the same locations.

        After sampling Location objects are shared between shared activity locations and corresponding
        trips start and end locations. These objects are mutable, so care must be taken if making changes
        as these will impact all other persons shared locations in the household. Often this behaviour
        might be expected. For example if we change the location of the household home activity, all
        persons and home activities are impacted.

        TODO - add method to all core classes
        """
        for _, household in self.households.items():
            home_loc = activity.Location(
                area=household.location.area,
                loc=sampler.sample(household.location.area, 'home')
            )

            unique_locations = {(household.location.area, 'home'): home_loc}

            for _, person in household.people.items():
                
                for act in person.activities:

                    # remove "escort_" from activity types.
                    if act.act[:7] == "escort_":
                        target_act = act.act[7:]
                    else:
                        target_act = act.act

                    if (act.location.area, target_act) in unique_locations:
                        location = unique_locations[(act.location.area, target_act)]
                        act.location = location
                            
                    else:
                        location = activity.Location(
                            area=act.location.area,
                            loc=sampler.sample(act.location.area, target_act)
                        )
                        unique_locations[(act.location.area, target_act)] = location
                        act.location = location

                # complete the alotting activity locations to the trip starts and ends.
                for idx in range(person.plan.length):
                    component = person.plan[idx]
                    if isinstance(component, activity.Leg):
                        component.start_location = person.plan[idx-1].location
                        component.end_location = person.plan[idx+1].location


class Household:
    logger = logging.getLogger(__name__)

    def __init__(self, hid, attributes=None):
        self.hid = str(hid)
        self.people = {}
        self.attributes = attributes

    def add(self, person):
        if not isinstance(person, Person):
            raise UserWarning(f"Expected instance of Person, not: {type(person)}")
        # person.finalise()
        self.people[str(person.pid)] = person

    def get(self, pid, default=None):
        return self.people.get(pid, default)

    def random_person(self):
        return self.people[random.choice(list(self.people))]

    def __getitem__(self, pid):
        return self.people[pid]

    def __iter__(self):
        for pid, person in self.people.items():
            yield pid, person

    @property
    def location(self):
        for person in self.people.values():
            if person.home is not None:
                return person.home
        self.logger.warning(f"Failed to find location for household: {self.hid}")

    @property
    def activity_classes(self):
        acts = set()
        for _, p in self:
            acts.update(p.activity_classes)
        return acts

    @property
    def mode_classes(self):
        modes = set()
        for _, p in self:
            modes.update(p.mode_classes)
        return modes

    def fix_plans(self, crop=True, times=True, locations=True):
        for person in self:
            if crop:
                person.plan.crop()
            if times:
                person.plan.fix_time_consistency()
            if locations:
                person.plan.fix_location_consistency()

    def shared_activities(self):
        shared_activities = []
        household_activities = []
        for pid, person in self.people.items():
            for activity in person.activities:
                if activity.isin_exact(household_activities):
                    shared_activities.append(activity)
                if not activity.isin_exact(household_activities):
                    household_activities.append(activity)
        return shared_activities

    def print(self):
        print(self)
        for _, person in self:
            person.print()

    def size(self):
        return len(self.people)

    def plot(self, kwargs=None):
        plot.plot_household(self, kwargs)

    def __str__(self):
        return f"Household: {self.hid}"

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)


class Person:
    logger = logging.getLogger(__name__)

    def __init__(self, pid, freq=1, attributes=None, home_area=None):
        self.pid = str(pid)
        self.freq = freq
        self.attributes = attributes
        self.plan = activity.Plan(home_area=home_area)
        self.home_area = home_area

    @property
    def home(self):
        if self.plan:
            return self.plan.home

    @property
    def activities(self):
        if self.plan:
            for act in self.plan.activities:
                yield act

    @property
    def num_activities(self):
        if self.plan:
            return len(list(self.activities))
        return 0

    @property
    def legs(self):
        if self.plan:
            for leg in self.plan.legs:
                yield leg

    @property
    def num_legs(self):
        if self.plan:
            return len(list(self.legs))
        return 0

    @property
    def length(self):
        return len(self.plan)

    def __len__(self):
        return self.length

    def __getitem__(self, val):
        return self.plan[val]

    def __iter__(self):
        for component in self.plan:
            yield component

    @property
    def activity_classes(self):
        return self.plan.activity_classes

    @property
    def mode_classes(self):
        return self.plan.mode_classes

    @property
    def has_valid_plan(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        return self.plan.is_valid

    def validate(self):
        """
        Validate plan.
        """
        self.plan.validate()
        return True

    def validate_sequence(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        if not self.plan.valid_sequence:
            raise PAMSequenceValidationError(f"Person {self.pid} has invalid plan sequence")

        return True

    def validate_times(self):
        """
        Check sequence of Activity and Leg times.
        :return: True
        """
        if not self.plan.valid_times:
            raise PAMTimesValidationError(f"Person {self.pid} has invalid plan times")

        return True

    def validate_locations(self):
        """
        Check sequence of Activity and Leg locations.
        :return: True
        """
        if not self.plan.valid_locations:
            raise PAMValidationLocationsError(f"Person {self.pid} has invalid plan locations")

        return True

    @property
    def closed_plan(self):
        """
        Check if plan starts and stops at the same facility (based on activity and location)
        :return: Bool
        """
        return self.plan.closed

    @property
    def first_activity(self):
        return self.plan.first

    @property
    def home_based(self):
        return self.plan.home_based

    def add(self, p):
        """
        Safely add a new component to the plan.
        :param p:
        :return:
        """
        self.plan.add(p)

    def finalise(self):
        """
        Add activity end times based on start time of next activity.
        """
        self.plan.finalise()

    def fix_plan(self, crop=True, times=True, locations=True):
        if crop:
            self.plan.crop()
        if times:
            self.plan.fix_time_consistency()
        if locations:
            self.plan.fix_location_consistency()

    def clear_plan(self):
        self.plan.clear()

    def print(self):
        print(self)
        print(self.attributes)
        self.plan.print()

    def plot(self, kwargs=None):
        plot.plot_person(self, kwargs)

    def __str__(self):
        return f"Person: {self.pid}"

    def remove_activity(self, seq):
        """
        Remove an activity from plan at given seq.
        Check for wrapped removal.
        Return (adjusted) idx of previous and subsequent activities as a tuple
        :param seq:
        :return: tuple
        """
        return self.plan.remove_activity(seq)

    def move_activity(self, seq, default='home'):
        """
        Move an activity from plan at given seq to default location
        :param seq:
        :param default: 'home' or pam.activity.Location
        :return: None
        """
        return self.plan.move_activity(seq, default)

    def fill_plan(self, p_idx, s_idx, default='home'):
        """
        Fill a plan after Activity has been removed.
        :param p_idx: location of previous Activity
        :param s_idx: location of subsequent Activity
        :param default:
        :return: bool
        """
        return self.plan.fill_plan(p_idx, s_idx, default=default)

    def stay_at_home(self):
        self.plan.stay_at_home()

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)
