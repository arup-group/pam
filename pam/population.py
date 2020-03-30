from datetime import datetime as dt


class Population:
    def __init__(self):
        self.households = {}

    def add(self, household):
        self.households[household.hid] = household


class HouseHold:
    def __init__(self, hid):
        self.hid = hid
        self.people = {}

    def add(self, person):
        self.people[person.pid] = person


class Person:
    def __init__(self, pid, freq=1, attributes=None):
        self.pid = pid
        self.freq = freq
        self.attributes = attributes
        self.activities = {}
        self.legs = {}

    def add(self, p):
        if isinstance(p, Activity):
            self.activities[p.seq] = p
        elif isinstance(p, Leg):
            self.legs[p.seq] = p
        else:
            raise UserWarning


class Activity:
    def __init__(self, seq, act, area, start_time=None, end_time=None):
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
    def __init__(
            self,
            seq,
            mode,
            start_loc=None,
            end_loc=None,
            start_time=None,
            end_time=None,
    ):
        self.seq = seq
        self.mode = mode
        self.start_loc = start_loc
        self.end_loc = end_loc
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

