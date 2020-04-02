from datetime import datetime
import pandas as pd


class Population:
    def __init__(self):
        self.households = {}

    def add(self, household):
        assert isinstance(household, HouseHold)
        self.households[household.hid] = household

    def load(self, trips_df, attributes_df):

        if isinstance(trips_df, pd.DataFrame) and isinstance(attributes_df, pd.DataFrame):
            self.load_from_df(trips_df, attributes_df)
        else:
            raise UserWarning("Unrecognised input for population")

    def load_from_df(self, trips_df, attributes_df):

        # todo deal with attributes_df

        """
        Turn tabular data inputs (population trips and attributes) into core population format.
        :param trips_df: DataDFrame
        :param attributes_df: DataDFrame
        :return: core.Population
        """

        for hid, household_data in trips_df.groupby('hid'):

            household = HouseHold(int(hid))

            for pid, person_data in household_data.groupby('pid'):

                # todo deal with agents not starting from home
                # tests/test_load.py::test_agent_pid_5_not_start_from_home

                trips = person_data.sort_values('seq')
                home_area = trips.hzone.iloc[0]
                activity_map = {home_area: 'home'}
                activities = ['home']

                person = Person(int(pid), freq=person_data.freq.iloc[0])
                person.add(
                    Activity(
                        seq=0,
                        act='home',
                        area=home_area,
                        start_time=minutes_to_datetime(0),
                    )
                )

                for n in range(len(trips)):
                    trip = trips.iloc[n]

                    destination_activity = trip.purp

                    person.add(
                        Leg(
                            seq=n,
                            mode=trip.mode,
                            start_loc=trip.ozone,
                            end_loc=trip.dzone,
                            start_time=minutes_to_datetime(trip.tst),
                            end_time=minutes_to_datetime(trip.tet)
                        )
                    )

                    if destination_activity in activities and activity_map.get(
                            trip.dzone):  # assume return trip to this activity
                        person.add(
                            Activity(
                                seq=n + 1,
                                act=activity_map[trip.dzone],
                                area=trip.dzone,
                                start_time=minutes_to_datetime(trip.tet),
                            )
                        )

                    else:
                        person.add(
                            Activity(
                                seq=n + 1,
                                act=trip.purp,
                                area=trip.dzone,
                                start_time=minutes_to_datetime(trip.tet),
                            )
                        )

                        if not trip.dzone in activity_map:  # update history
                            activity_map[
                                trip.dzone] = trip.purp  # only keeping first activity at each location to ensure returns home

                        activities.append(destination_activity)

                household.add(person)

            self.add(household)


class HouseHold:
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

    def clear_plan(self):
        self.plan = []

    def add(self, p):
        if isinstance(p, Activity):
            assert not self.plan or isinstance(self.plan[-1], Leg)  # enforce act-leg-act seq
            self.plan.append(p)
        elif isinstance(p, Leg):
            assert isinstance(self.plan[-1], Activity)  # enforce act-leg-act seq
            self.plan.append(p)
        else:
            raise UserWarning

    def finalise(self):
        """
        Add activity end times based on start time of next activity
        """
        if len(self.plan) > 1:
            for seq in range(0, len(self.plan)-1, 2):  # activities excluding last one
                self.plan[seq].end_time = self.plan[seq+1].start_time
        self.plan[-1].end_time = minutes_to_datetime(24 * 60 - 1)

    def validate(self):
        """
        validate the sequence of the plan and correctly ordered datetimes.
        """
        # todo
        assert isinstance(self.plan[-1], Activity)


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
            start_loc=None,
            end_loc=None,
            start_time=None,
            end_time=None,
    ):
        # todo deal with times

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


def minutes_to_datetime(minutes):
    """
    Convert minutes to datetime
    :param minutes: int
    :return: datetime
    """
    assert minutes < 24 * 60
    hours = minutes // 60
    minutes = minutes % 60
    return datetime(2020, 4, 2, hours, minutes)


