import logging
import random
import pickle

from .activity import Plan
from .plot import plot_person, plot_household


class Population:

    def __init__(self, name=None):
        self.name=name
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

    def random_household(self):
        return self.households[random.choice(list(self.households))]
    
    def random_person(self):
        hh = self.random_household()
        return hh.random_person()

    def people_count(self):
        count = 0
        for hid, household in self.households.items():
            count += household.size()
        return count

    @property
    def size(self):
        return sum([person.freq for _, _, person in self.people()])

    def count(self, households=False):
        if households:
            return len(self.households)
        return len(list(self.people()))

    def print(self):
        print(self)
        for _, household in self:
            household.print()

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)

    def __str__(self):
        return f"Population: {self.people_count()} people in {self.count(households=True)} households."


class Household:
    logger = logging.getLogger(__name__)

    def __init__(self, hid):
        
        if not isinstance(hid, str):
            hid = str(hid)
            self.logger.warning(" converting household id to string")
        self.hid = hid
        self.people = {}
        self.area = None

    def add(self, person):
        person.finalise()
        self.people[str(person.pid)] = person
        self.area = person.home

    def get(self, pid, default=None):
        return self.people.get(pid, default)

    def random_person(self):
        return self.people[random.choice(list(self.people))]

    def __getitem__(self, pid):
        return self.people[pid]

    def __iter__(self):
        for pid, person in self.people.items():
            yield pid, person

    def size(self):
        return len(self.people)

    def print(self):
        print(self)
        for _, person in self:
            person.print()

    def plot(self):
        plot_household(self)

    def __str__(self):
        return f"Household: {self.hid}"

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)

class Person:
    logger = logging.getLogger(__name__)

    def __init__(self, pid, freq=1, attributes=None, home_area=None):
        if not isinstance(pid, str):
            pid = str(pid)
            self.logger.warning(" converting person id to string")
        self.pid = str(pid)
        self.freq = freq
        self.attributes = attributes
        self.plan = Plan(home_area=home_area)
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
    def legs(self):
        if self.plan:
            for leg in self.plan.legs:
                yield leg

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
    def has_valid_plan(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        return self.plan.is_valid

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

    def clear_plan(self):
        self.plan.clear()

    def print(self):
        print(self)
        print(self.attributes)
        self.plan.print()

    def plot(self):
        plot_person(self)

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
