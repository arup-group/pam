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
                if p.act.lower() == 'home':
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
    def length(self):
        return len(self.plan)

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
            raise TypeError(f"Person plan does not end with Activity")

        if not self.plan[0].start_time == minutes_to_datetime(0):
            raise TypeError("First activity does not start at zero")

        for i in range(self.length - 1):
            if not self.plan[i].end_time == self.plan[i+1].start_time:
                raise TypeError("Miss-match in adjoining activity end and start times")

        if not self.plan[-1].end_time == minutes_to_datetime(24*60-1):
            raise TypeError("Last activity does not end at 23:59:59")

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

    def position_of(self, act='home'):
        last = None
        for seq, act in enumerate(self.plan):
            if act.act.lower() == 'home':
                last = seq
        return last

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

    def print_plan(self):
        for seq, component in enumerate(self.plan):
            print(f"{seq}:\t{component}")

    def remove_activity(self, seq):
        """
        Remove an activity from plan at given seq.
        Check for wrapped removal.
        Return (adjusted) idx of previous and subsequent activities as a tuple
        :param seq:
        :return: tuple
        """
        assert isinstance(self.plan[seq], Activity)

        if (seq == 0 or seq == self.length - 1) and self.closed_plan:  # remove pair
            self.plan.pop(0)
            self.plan.pop(self.length - 1)
            return self.length-2, 1

        elif seq == 0:  # remove first act
            self.plan.pop(seq)
            return None, 1

        elif seq == self.length - 1:  # remove last act
            self.plan.pop(seq)
            return self.length-2, None

        else:  # remove act is somewhere in middle of plan
            self.plan.pop(seq)
            return seq-2, seq+1

    def fill_plan(self, p_idx, s_idx, default='home'):
        """
        Fill a plan after Activity has been removed.
        :param p_idx: location of previous Activity
        :param s_idx: location of subsequent Activity
        :param default:
        :return: True
        """

        if p_idx is not None and s_idx is not None:  # regular middle of plan activity

            if self.plan[p_idx] == self.plan[s_idx]:  # combine activities

                if p_idx == s_idx:  # this is a single remaining activity -> stay at home

                    if self.position_of(act='home') is None:
                        raise ValueError(
                            "Require home activity"
                        )
                    self.plan = self.stay_at_home()
                    return True

                if s_idx < p_idx:  # this is a wrapped activity --> close it
                    # todo probably don't need to pass the idx - know that it must be first and last
                    self.combine_wrapped_activities(p_idx, s_idx)
                    return True

                # this is a regular non wrapped mid plan activity -> combine acts
                self.combine_matching_activities(p_idx, s_idx)
                return True

            # this plan cannot be closed - the proceeding and subs acts are not the same

            if s_idx < p_idx:  # this is a wrapped activity --> close it
                self.plan.pop(0)  # remove start leg
                self.plan.pop(-1)  # remove end leg

                pivot_idx = self.position_of(act='home')
                if pivot_idx is None:
                    raise NotImplementedError("Cannot fill plan without existing home activity")

                self.expand(pivot_idx)
                return True

            # need to change first leg for new destination
            self.join_activities(p_idx, s_idx)
            return True

        if p_idx is None:  # start of day non wrapping
            self.plan.pop(0)
            self.expand(s_idx-1)  # shifted because we popped index 0
            return True

        if s_idx is None:  # end of day non wrapping
            self.plan.pop(-1)
            self.expand(p_idx)
            return True

    def join_activities(self, p_idx, s_idx):
        """Join two Activities with new Leg, expand last home activity"""
        self.plan[p_idx + 1].end_area = self.plan[s_idx - 1].end_area
        self.plan.pop(s_idx - 1)  # remove second leg

        # todo add logic to change mode and time of leg

        # press plans away from pivoting activity
        pivot_idx = self.position_of(act='home')
        if pivot_idx is None:
            raise NotImplementedError(
                f"Cannot fill plan without existing home activity @ {self.pid}"
            )

        self.expand(pivot_idx)

    def combine_matching_activities(self, p_idx, s_idx):
        """Combine given Activities, remove surplus Legs"""
        self.plan[p_idx].end_time = self.plan[s_idx].end_time  # extend proceeding act
        self.plan.pop(s_idx)  # remove subsequent activity
        self.plan.pop(s_idx - 1)  # remove subsequent leg
        self.plan.pop(p_idx + 1)  # remove proceeding leg

    def combine_wrapped_activities(self, p_idx, s_idx):
        """Combine given Activities, remove surplus Legs"""
        # extend proceeding act to end of day
        self.plan[p_idx].end_time = minutes_to_datetime(24 * 60 - 1)
        # extend subsequent act to start of day
        self.plan[s_idx].start_time = minutes_to_datetime(0)
        self.plan.pop(p_idx + 1)  # remove proceeding leg
        self.plan.pop(s_idx - 1)  # remove subsequent leg
        return True

    def expand(self, pivot_idx):
        # todo this isn't great - just pushes other activities to edges of day

        new_time = minutes_to_datetime(0)
        for seq in range(pivot_idx+1):  # push forward pivot and all proceeding components
            new_time = self.plan[seq].shift_start_time(new_time)

        new_time = minutes_to_datetime(24*60-1)
        for seq in range(self.length-1, pivot_idx, -1):  # push back all subsequent components
            new_time = self.plan[seq].shift_end_time(new_time)

        self.plan[pivot_idx].end_time = new_time  # expand pivot

    def stay_at_home(self):
        return [
            Activity(
                seq=1,
                act='home',
                area=self.home,
                start_time=minutes_to_datetime(0),
                end_time=minutes_to_datetime(24 * 60 - 1),
            )
        ]


class PlanComponent:

    @property
    def duration(self):
        return self.end_time - self.start_time

    def shift_start_time(self, new_start_time):
        duration = self.duration
        self.start_time = new_start_time
        self.end_time = new_start_time + duration
        return self.end_time

    def shift_end_time(self, new_end_time):
        duration = self.duration
        self.end_time = new_end_time
        self.start_time = new_end_time - duration
        return self.start_time


class Activity(PlanComponent):

    def __init__(self, seq, act, area, start_time=None, end_time=None):
        # todo deal with times
        self.seq = seq
        self.act = act
        self.area = area
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f"Activity(act:{self.act}, area:{self.area}, " \
               f"time:{self.start_time.time()} --> {self.end_time.time()}, " \
               f"duration:{self.duration})"

    def __eq__(self, other):
        return (other.act, other.area) == (self.act, self.area)


class Leg(PlanComponent):

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

    def __str__(self):
        return f"Leg(mode:{self.mode}, area:{self.start_area} --> " \
               f"{self.end_area}, time:{self.start_time.time()} --> {self.end_time.time()}, " \
               f"duration:{self.duration})"


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

