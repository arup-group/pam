from .utils import minutes_to_datetime as mtdt


class Plan:
    
    def __init__(self):
        self.day = []

    @property
    def home(self):
        if self.day:
            for act in self.activities:
                if act.act.lower() == 'home':
                    return act.area

    @property
    def activities(self):
        for p in self.day:
            if isinstance(p, Activity):
                yield p

    @property
    def legs(self):
        for p in self.day:
            if isinstance(p, Leg):
                yield p

    @property
    def closed(self):
        """
        Check if plan starts and stops at the same facility (based on activity and location)
        :return: Bool
        """
        if self.day[0] == self.day[-1]:
            return True
        return False

    @property
    def first(self):
        return self.day[0].act

    @property
    def last(self):
        return self.day[-1].act

    @property
    def home_based(self):
        return self.first.lower() == 'home'

    @property
    def length(self):
        return len(self.day)

    def __iter__(self):
        for component in self.day:
            yield component

    def reversed(self):
        """
        Reverse iterate through plan, yield idx and component.
        """
        for i in range(self.length-1, -1, -1):
            yield i, self[i]

    def __len__(self):
        return self.length

    def __getitem__(self, val):
        return self.day[val]

    def __eq__(self, other):
        """
        Note that this only checks for equality of location and activity
        """
        if not isinstance(other, Plan):
            raise UserWarning(f"Cannot compare plan to non plan ({type(other)})")
        for i, j in zip(self, other):
            if not i == j:
                return False
        return True

    @property
    def is_valid(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        for i, component in enumerate(self.day):
            if i % 2:  # uneven
                if not isinstance(component, Leg):
                    raise TypeError(f"Incorrect plan sequence")
            else:
                if not isinstance(component, Activity):
                    raise TypeError(f"Incorrect plan sequence")

        if not isinstance(self.day[-1], Activity):
            raise TypeError(f"Person plan does not end with Activity")

        if not self.day[0].start_time == mtdt(0):
            raise TypeError("First activity does not start at zero")

        for i in range(self.length - 1):
            if not self.day[i].end_time == self.day[i+1].start_time:
                raise TypeError("Miss-match in adjoining activity end and start times")

        if not self.day[-1].end_time == mtdt(24*60-1):
            raise TypeError("Last activity does not end at 23:59:59")

        return True

    def position_of(self, target='home', search='last'):
        """
        Return position of target activity type (either first or last depending on search).
        Return None if not found.
        :param target: str
        :param search: str {'first', 'last'}
        :return: {int, None}
        """

        if search not in ['last', 'first']:
            raise UserWarning("Method only supports search types 'first' or 'last'.")

        if search == 'last':
            last = None
            for seq, act in enumerate(self.day):
                if act.act.lower() == target:
                    last = seq
            return last

        if search == 'first':
            for seq, act in enumerate(self.day):
                if act.act.lower() == target:
                    return seq

    def add(self, p):
        """
        Safely add a new component to the plan.
        :param p:
        :return:
        """
        if isinstance(p, Activity):
            if self.day and not isinstance(self.day[-1], Leg):  # enforce act-leg-act seq
                raise UserWarning(f"Cannot add Activity to plan sequence.")
            self.day.append(p)

        elif isinstance(p, Leg):
            if not self.day:
                raise UserWarning(f"Cannot add Leg as first component to plan sequence.")
            if not isinstance(self.day[-1], Activity):  # enforce act-leg-act seq
                raise UserWarning(f"Cannot add Leg to plan sequence.")
            self.day.append(p)

        else:
            raise UserWarning(f"Cannot add type: {type(p)} to plan.")

    def finalise(self):
        """
        Add activity end times based on start time of next activity.
        """
        if len(self.day) > 1:
            for seq in range(0, len(self.day)-1, 2):  # activities excluding last one
                self.day[seq].end_time = self.day[seq+1].start_time
        self.day[-1].end_time = mtdt(24 * 60 - 1)

    def clear(self):
        self.day = []

    def print(self):
        for seq, component in enumerate(self):
            print(f"{seq}:\t{component}")

    def remove_activity(self, seq):
        """
        Remove an activity from plan at given seq. Does not remove adjacent legs
        Will also check if an activity is wrapped and remove accordingly. Returns (adjusted) idx
        of previous (p_idx) and subsequent (s_idx) activities as a tuple. If there is no previous
        or subsequent activity, ie a removed activity is at the start or end of an open plan,
        then None can be returned. If all activities are removed then None, None is returned.
        :param seq: int
        :return: tuple
        """
        assert isinstance(self.day[seq], Activity)

        if seq == 0 and seq == self.length - 1:  # remove activity that is entire plan
            self.day.pop(0)
            return None, None

        if (seq == 0 or seq == self.length - 1) and self.closed:  # remove activity that wraps
            self.day.pop(0)
            self.day.pop(self.length - 1)
            return self.length-2, 1

        if seq == 0:  # remove first activity
            self.day.pop(seq)
            return None, 1

        if seq == self.length - 1:  # remove last activity
            self.day.pop(seq)
            return self.length-2, None

        else:  # remove activity somewhere in middle of plan
            self.day.pop(seq)
            return seq-2, seq+1

    def fill_plan(self, idx_start, idx_end, default='home'):
        """
        Fill a plan after Activity has been removed. Plan is filled between given remaining
        activity locations (idx_start and idx_end). Note that the plan will also have legs that
        need to be removed.
        :param idx_start: location of previous Activity
        :param idx_end: location of subsequent Activity
        :param default: Not Used
        :return: True
        """
        if idx_start is None and idx_end is None:  # Assume stay at home
            self.stay_at_home()
            return True

        if idx_start is None:  # start of day non wrapping
            self.day.pop(0)
            self.expand(idx_end - 1)  # shifted because we popped index 0
            return True

        if idx_end is None:  # end of day non wrapping
            self.day.pop(-1)
            self.expand(idx_start)
            return True

        if idx_start == idx_end:  # this is a single remaining activity -> stay at home

            if self.position_of(target='home') is None:
                raise ValueError(
                    "Require home activity"
                )
            self.stay_at_home()
            return True

        if self.day[idx_start] == self.day[idx_end]:  # combine activities
            """
            These activities are the same (based on type and location), so can be combined, 
            but there are 2 sub cases:
            i) idx_start < idx_end -> wrapped combine
            ii) else -> regular combine can ignore wrapping
            """

            if idx_end < idx_start:  # this is a wrapped activity --> close it
                # todo probably don't need to pass the idx - know that it must be first and last
                self.combine_wrapped_activities(idx_start, idx_end)
                return True

            # this is a regular non wrapped mid plan activity -> combine acts
            self.combine_matching_activities(idx_start, idx_end)
            return True

        """
        Remaining are plans where the activities are different so fill not be combined, instread 
        we will use 'expand' to refill the plan. There are 2 sub cases:
        i) idx_start < idx_end -> wrapped combine
        ii) else -> regular combine can ignore wrapping
        """

        if idx_end < idx_start:  # this is a wrapped activity --> close it
            self.day.pop(0)  # remove start leg
            self.day.pop(-1)  # remove end leg

            pivot_idx = self.position_of(target='home')
            if pivot_idx is None:
                raise NotImplementedError("Cannot fill plan without existing home activity")

            self.expand(pivot_idx)
            return True

        # need to change first leg for new destination
        self.join_activities(idx_start, idx_end)
        return True

    def expand(self, pivot_idx):
        """
        Fill plan by expanding a pivot activity.
        :param pivot_idx: int
        :return: None
        """
        # todo this isn't great - just pushes other activities to edges of day

        new_time = mtdt(0)
        for seq in range(pivot_idx+1):  # push forward pivot and all proceeding components
            new_time = self.day[seq].shift_start_time(new_time)

        new_time = mtdt(24*60-1)
        for seq in range(self.length-1, pivot_idx, -1):  # push back all subsequent components
            new_time = self.day[seq].shift_end_time(new_time)

        self.day[pivot_idx].end_time = new_time  # expand pivot

    def join_activities(self, idx_start, idx_end):
        """
        Join together two Activities with new Leg, expand last home activity.
        :param idx_start:
        :param idx_end:
        :return:
        """
        self.day[idx_start + 1].end_area = self.day[idx_end - 1].end_area
        self.day.pop(idx_end - 1)  # remove second leg

        # todo add logic to change mode and time of leg

        # press plans away from pivoting activity
        pivot_idx = self.position_of(target='home')
        if pivot_idx is None:
            raise NotImplementedError(
                f"Cannot fill plan without existing home activity"
            )

        self.expand(pivot_idx)

    def combine_matching_activities(self, idx_start, idx_end):
        """
        Combine two given activities into same activity, remove surplus Legs
        :param idx_start:
        :param idx_end:
        :return:
        """
        self.day[idx_start].end_time = self.day[idx_end].end_time  # extend proceeding act
        self.day.pop(idx_end)  # remove subsequent activity
        self.day.pop(idx_end - 1)  # remove subsequent leg
        self.day.pop(idx_start + 1)  # remove proceeding leg

    def combine_wrapped_activities(self, idx_start, idx_end):
        """
        Combine two given activities that will wrap around day, remove surplus Legs
        :param idx_start:
        :param idx_end:
        :return:
        """
        # extend proceeding act to end of day
        self.day[idx_start].end_time = mtdt(24 * 60 - 1)
        # extend subsequent act to start of day
        self.day[idx_end].start_time = mtdt(0)
        self.day.pop(idx_start + 1)  # remove proceeding leg
        self.day.pop(idx_end - 1)  # remove subsequent leg
        return True

    def stay_at_home(self):
        self.day = [
            Activity(
                seq=1,
                act='home',
                area=self.home,
                start_time=mtdt(0),
                end_time=mtdt(24 * 60 - 1),
            )
        ]

    def simplify_pt_trips(self):
        """
        Remove pt interaction events (resulting from complex matsim plans), simplify legs
        to single leg with mode = pt
        """
        pt_trip = False
        for idx, component in list(self.reversed()):
            if component.act == "pt interaction":  # this is a pt trip
                if not pt_trip:  # this is a new pt leg
                    trip_end_time = self[idx+1].end_time
                    trip_end_loc = self[idx+1].end_loc
                    trip_end_link = self[idx+1].end_link
                    trip_end_area = self[idx+1].end_area

                pt_trip = True
                self.day.pop(idx+1)
                self.day.pop(idx)
            else:
                if pt_trip:  # this is the start of the pt trip - modify the first leg
                    self[idx].mode = 'pt'
                    self[idx].end_time = trip_end_time
                    self[idx].end_loc = trip_end_loc
                    self[idx].end_link = trip_end_link
                    self[idx].end_area = trip_end_area
                pt_trip = False


class PlanComponent:

    @property
    def duration(self):
        return self.end_time - self.start_time

    def shift_start_time(self, new_start_time):
        """
        Given a new start time, set start time, set end time based on previous duration and
        return new end time.
        :param new_start_time: datetime
        :return: datetime
        """
        duration = self.duration
        self.start_time = new_start_time
        self.end_time = new_start_time + duration
        return self.end_time

    def shift_end_time(self, new_end_time):
        """
        Given a new end time, set end time, set start time based on previous duration and
        return new start time.
        :param new_end_time: datetime
        :return: datetime
        """
        duration = self.duration
        self.end_time = new_end_time
        self.start_time = new_end_time - duration
        return self.start_time


class Activity(PlanComponent):

    def __init__(
            self,
            seq=None,
            act=None,
            loc=None,
            link=None,
            area=None,
            start_time=None,
            end_time=None
            ):
        self.seq = seq
        self.act = act
        self.loc = loc
        self.link = link
        self.area = area
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        location = self.loc
        if self.area:
            location = self.area
        return f"Activity({self.seq} act:{self.act}, location:{location}, " \
               f"time:{self.start_time.time()} --> {self.end_time.time()}, " \
               f"duration:{self.duration})"

    def __eq__(self, other):
        if self.loc and other.loc:
            return (other.act, other.loc) == (self.act, self.loc)
        if self.link and other.link:
            return (other.act, other.link) == (self.act, self.link)
        if self.area and other.area:
            return (other.act, other.area) == (self.act, self.area)
        raise UserWarning(
    "Cannot check for act equality without same loc types (areas/locs/links)."
    )


class Leg(PlanComponent):

    act = 'travel'

    def __init__(
            self,
            seq=None,
            mode=None,
            start_loc=None,
            end_loc=None,
            start_link=None,
            end_link=None,
            start_area=None,
            end_area=None,
            start_time=None,
            end_time=None,
    ):
        self.seq = seq
        self.mode = mode
        self.start_loc=start_loc
        self.end_loc=end_loc
        self.start_link=start_link
        self.end_link=end_link
        self.start_area = start_area
        self.end_area = end_area
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        start, end = self.start_loc, self.end_loc
        if self.start_area:
            start = self.start_area
        if self.end_area:
            end = self.end_area
        return f"Leg({self.seq} mode:{self.mode}, area:{start} --> " \
               f"{end}, time:{self.start_time.time()} --> {self.end_time.time()}, " \
               f"duration:{self.duration})"

    def __eq__(self, other):
        return (other.mode, other.duration) == (self.mode, self.duration)

