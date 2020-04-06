from datetime import datetime


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
        self.plan = []

    @property
    def home(self):
        if self.plan:
            for p in self.plan:
                if p.act == 'home':
                    return p.area

    @property
    def activities(self):
        for p in self.plan:
            if isinstance(p, Activity):
                yield p

    @property
    def legs(self):
        for p in self.plan:
            if isinstance(p, Leg):
                yield p

    @property
    def valid_plan(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        for i, component in enumerate(self.plan):
            if i % 2:  # uneven
                if not isinstance(component, Leg):
                    raise TypeError(f"Person {self.pid} incorrect plan sequence")
            else:
                if not isinstance(component, Activity):
                    raise TypeError(f"Person {self.pid} incorrect plan sequence")

        if not isinstance(self.plan[-1], Activity):
            raise TypeError(f"Person {self.pid} plan does not end with Activity")
        return True

    @property
    def closed_plan(self):
        """
        Check if plan starts and stops at the same facility (based on activity and location)
        :return: Bool
        """
        if (self.plan[0].act, self.plan[0].area) == (self.plan[-1].act, self.plan[-1].area):
            return True
        return False

    @property
    def first_activity(self):
        return self.plan[0].act

    @property
    def home_based(self):
        return self.first_activity.lower() == 'home'

    def add(self, p):
        """
        Safely add a new component to the plan.
        :param p:
        :return:
        """
        if isinstance(p, Activity):
            if self.plan and not isinstance(self.plan[-1], Leg):  # enforce act-leg-act seq
                raise UserWarning(f"Cannot add Activity to plan sequence.")
            self.plan.append(p)
        elif isinstance(p, Leg):
            if not self.plan:
                raise UserWarning(f"Cannot add Leg as first component to plan sequence.")
            if not isinstance(self.plan[-1], Activity):  # enforce act-leg-act seq
                raise UserWarning(f"Cannot add Leg to plan sequence.")
            self.plan.append(p)
        else:
            raise UserWarning(f"Cannot add type: {type(p)} to plan.")

    def finalise(self):
        """
        Add activity end times based on start time of next activity.
        """
        if len(self.plan) > 1:
            for seq in range(0, len(self.plan)-1, 2):  # activities excluding last one
                self.plan[seq].end_time = self.plan[seq+1].start_time
        self.plan[-1].end_time = minutes_to_datetime(24 * 60 - 1)

    def clear_plan(self):
        self.plan = []


class Activity:
    def __init__(self, seq, act, area, start_time=None, end_time=None):
        # todo deal with times
        self.seq = seq
        self.act = act
        self.area = area
        self.start_time = start_time
        self.end_time = end_time
        # self.start_time_dt = dt.strptime(self.start_time, '%H:%M:%S')
        # self.end_time_dt = dt.strptime(self.end_time, '%H:%M:%S')
        # self.start_time_minutes = self.start_time_dt.hour * 60 + self.start_time_dt.minute
        # self.end_time_minutes = self.end_time_dt.hour * 60 + self.end_time_dt.minute
        # self.duration = self.end_time_minutes - self.start_time_minutes
        # if self.duration < 0:
        #     self.duration = (24 * 60) + self.duration


class Leg:

    act = 'travel'

    def __init__(
            self,
            seq,
            mode,
            start_area=None,
            end_area=None,
            start_time=None,
            end_time=None,
    ):
        # todo deal with times

        self.seq = seq
        self.mode = mode
        self.start_area = start_area
        self.end_area = end_area
        self.start_time = start_time
        self.end_time = end_time
        # self.start_time_dt = dt.strptime(start_time, '%H:%M:%S')
        # self.end_time_dt = dt.strptime(end_time, '%H:%M:%S')
        # self.start_time_minutes = self.start_time_dt.hour * 60 + self.start_time_dt.minute
        # self.end_time_minutes = self.end_time_dt.hour * 60 + self.end_time_dt.minute
        # self.duration = self.end_time_minutes - self.start_time_minutes
        # self.dist = dist
        # if self.duration < 0:
        #     self.duration = (24 * 60) + self.duration


def minutes_to_datetime(minutes: int):
    """
    Convert minutes to datetime
    :param minutes: int
    :return: datetime
    """
    assert minutes < 24 * 60
    hours = minutes // 60
    minutes = minutes % 60
    return datetime(2020, 4, 2, hours, minutes)
