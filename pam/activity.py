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
        if (self.day[0].act, self.day[0].area) == (self.day[-1].act, self.day[-1].area):
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

    def __len__(self):
        return self.length

    def __getitem__(self, val):
        return self.day[val]

    def validate(self):
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
        Remove an activity from plan at given seq.
        Check for wrapped removal.
        Return (adjusted) idx of previous and subsequent activities as a tuple
        :param seq:
        :return: tuple
        """
        assert isinstance(self.day[seq], Activity)

        if (seq == 0 or seq == self.length - 1) and self.closed:  # remove pair
            self.day.pop(0)
            self.day.pop(self.length - 1)
            return self.length-2, 1

        elif seq == 0:  # remove first act
            self.day.pop(seq)
            return None, 1

        elif seq == self.length - 1:  # remove last act
            self.day.pop(seq)
            return self.length-2, None

        else:  # remove act is somewhere in middle of plan
            self.day.pop(seq)
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

            if self.day[p_idx] == self.day[s_idx]:  # combine activities

                if p_idx == s_idx:  # this is a single remaining activity -> stay at home

                    if self.position_of(target='home') is None:
                        raise ValueError(
                            "Require home activity"
                        )
                    self.stay_at_home()
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
                self.day.pop(0)  # remove start leg
                self.day.pop(-1)  # remove end leg

                pivot_idx = self.position_of(target='home')
                if pivot_idx is None:
                    raise NotImplementedError("Cannot fill plan without existing home activity")

                self.expand(pivot_idx)
                return True

            # need to change first leg for new destination
            self.join_activities(p_idx, s_idx)
            return True

        # todo can both p_idx and s_idx be None? ie if a removed act is entire plan?

        if p_idx is None:  # start of day non wrapping
            self.day.pop(0)
            self.expand(s_idx-1)  # shifted because we popped index 0
            return True

        if s_idx is None:  # end of day non wrapping
            self.day.pop(-1)
            self.expand(p_idx)
            return True

    def join_activities(self, p_idx, s_idx):
        """Join two Activities with new Leg, expand last home activity"""
        self.day[p_idx + 1].end_area = self.day[s_idx - 1].end_area
        self.day.pop(s_idx - 1)  # remove second leg

        # todo add logic to change mode and time of leg

        # press plans away from pivoting activity
        pivot_idx = self.position_of(target='home')
        if pivot_idx is None:
            raise NotImplementedError(
                f"Cannot fill plan without existing home activity"
            )

        self.expand(pivot_idx)

    def combine_matching_activities(self, p_idx, s_idx):
        """Combine given Activities, remove surplus Legs"""
        self.day[p_idx].end_time = self.day[s_idx].end_time  # extend proceeding act
        self.day.pop(s_idx)  # remove subsequent activity
        self.day.pop(s_idx - 1)  # remove subsequent leg
        self.day.pop(p_idx + 1)  # remove proceeding leg

    def combine_wrapped_activities(self, p_idx, s_idx):
        """Combine given Activities, remove surplus Legs"""
        # extend proceeding act to end of day
        self.day[p_idx].end_time = mtdt(24 * 60 - 1)
        # extend subsequent act to start of day
        self.day[s_idx].start_time = mtdt(0)
        self.day.pop(p_idx + 1)  # remove proceeding leg
        self.day.pop(s_idx - 1)  # remove subsequent leg
        return True

    def expand(self, pivot_idx):
        # todo this isn't great - just pushes other activities to edges of day

        new_time = mtdt(0)
        for seq in range(pivot_idx+1):  # push forward pivot and all proceeding components
            new_time = self.day[seq].shift_start_time(new_time)

        new_time = mtdt(24*60-1)
        for seq in range(self.length-1, pivot_idx, -1):  # push back all subsequent components
            new_time = self.day[seq].shift_end_time(new_time)

        self.day[pivot_idx].end_time = new_time  # expand pivot

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

    def __init__(self, seq=None, act=None, area=None, start_time=None, end_time=None):
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
            seq=None,
            mode=None,
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
