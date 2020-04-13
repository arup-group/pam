from .activity import Plan


class Population:
    def __init__(self):
        self.households = {}

    def add(self, household):
        assert isinstance(household, Household)
        self.households[household.hid] = household


class Household:
    def __init__(self, hid):
        self.hid = hid
        self.people = {}
        self.area = None

    def add(self, person):
        person.finalise()
        self.people[person.pid] = person
        self.area = person.home


class Person:
    def __init__(self, pid, freq=1, attributes=None):
        self.pid = pid
        self.freq = freq
        self.attributes = attributes
        self.plan = Plan()

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
    def valid_plan(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        return self.plan.validate()

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

    def print_plan(self):
        self.plan.print()

    def remove_activity(self, seq):
        """
        Remove an activity from plan at given seq.
        Check for wrapped removal.
        Return (adjusted) idx of previous and subsequent activities as a tuple
        :param seq:
        :return: tuple
        """
        return self.plan.remove_activity(seq)

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
