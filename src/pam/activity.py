from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from copy import copy
from datetime import timedelta
from typing import Any, Literal, Optional, Union

from numpy import datetime64

import pam.utils as utils
import pam.variables
from pam import (
    InvalidMATSimError,
    PAMInvalidTimeSequenceError,
    PAMSequenceValidationError,
    PAMValidationLocationsError,
)
from pam.location import Location
from pam.plot import plans as plot
from pam.variables import END_OF_DAY


class Plan:
    def __init__(
        self, home_area=None, home_location: Optional[Location] = None, home_loc=None, freq=None
    ):
        self.day = []
        if home_location:
            self.home_location = home_location
        else:
            self.home_location = Location()
        if home_area:
            self.home_location.area = home_area
        if home_loc:
            self.home_location.loc = home_loc
        self.logger = logging.getLogger(__name__)
        self.plan_freq = freq
        self.score = None

    @property
    def home(self):
        if self.home_location.exists:
            return self.home_location
        if self.day:
            for act in self.activities:
                if act.act is not None and act.act.lower()[:4] == "home":
                    return act.location
        return self.day[0].location

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

    def simplify_pt_trips(self, ignore=["pt interaction", "pt_interaction"]) -> None:
        """Remove public transit (pt) interaction events and simplify associated legs to single legs with
        dominant mode. Dominant mode is based on max (total) distance by each mode.

        For example, given the following trip:

            home =walk=> pt interaction =bus=> pt interaction =walk=> work

        Is simplified to:

            home =bus=> work

        (In this example we are assuming that bus was used to travel further than the two walk legs). The final
        bus leg duration and distance are taken from the accumulated walk and bus leg durations and distances.

        Args:
          ignore (list[str], optional): activities to remove. Defaults to ["pt interaction", "pt_interaction"].

        """
        if set(ignore).intersection(self.activity_classes):
            self.day = list(self.tripify(ignore=ignore))

    def tripify(
        self, ignore: list[str] = ["pt interaction", "pt_interaction"]
    ) -> Iterator[PlanComponent]:
        """Iterate through plan components removing public transit (pt) interaction events and simplifying
        associated legs to single leg with dominant mode. Where dominant mode is based on max (total) distance
        by each mode for that trip.

        For example, given the following trip:

            home =walk=> pt interaction =bus=> pt interaction =walk=> work

        Is "tripified" to:

            home =bus=> work

        (In this example we are assuming that bus was used to travel further than the two walk legs). The final
        bus leg duration and distance are taken from the accumulated walk and bus leg durations and distances.

        Args:
          ignore (list[str], optional): activities to remove. Defaults to ["pt interaction", "pt_interaction"].

        Returns:
            Iterator[PlanComponent]
        """
        if self.day:
            seq = 0
            modes = {}
            start_location = self.day[0].location
            start_time = self.day[0].end_time
            distance = 0
            for component in self:
                if isinstance(component, Leg):
                    modes[component.mode] = modes.get(component.mode, 0) + component.distance
                    distance += component.distance
                    attributes = component.attributes  # trips collect attributes from last leg
                if isinstance(component, Activity):
                    if component.act not in ignore:
                        while True:
                            if modes:
                                yield Leg(
                                    seq=seq,
                                    mode=max(modes, key=modes.get),
                                    start_area=start_location.area,
                                    end_area=component.location.area,
                                    start_link=start_location.link,
                                    end_link=component.location.link,
                                    start_loc=start_location.loc,
                                    end_loc=component.location.loc,
                                    start_time=start_time,
                                    end_time=component.start_time,
                                    distance=distance,
                                    purp=component.act,
                                    attributes=attributes,
                                )
                            yield component
                            break
                        modes = {}
                        start_location = component.location
                        start_time = component.end_time
                        distance = 0
                        seq += 1

    def trips(self, ignore: list[str] = ["pt interaction", "pt_interaction"]) -> str:
        """Iterate through plan trips. Multi-modal leg trips are simplified to single trip with dominant mode.
        Where dominant mode is based on max (total) distance by each mode for that trip. The logic is based on
        the removal of public transit interaction activities.

        For example, given the following legs:

            home =walk=> pt interaction =bus=> pt interaction =walk=> work

        Is simplified to:

            home =bus=> work

        (In this example we are assuming that bus was used to travel further than the two walk legs). The final
        bus leg duration and distance are taken from the accumulated walk and bus leg durations and distances.

        Args:
          ignore (list[str], optional): activities to remove. Defaults to ["pt interaction", "pt_interaction"].

        Returns:
            Iterator[Trip]
        """
        if self.day:
            seq = 0
            modes = {}
            start_location = self.day[0].location
            start_time = self.day[0].end_time
            distance = 0
            for component in self[1:]:
                if isinstance(component, Leg):
                    modes[component.mode] = modes.get(component.mode, 0) + component.distance
                    distance += component.distance
                    attributes = component.attributes
                elif component.act not in ignore:
                    yield Trip(
                        seq=seq,
                        mode=max(modes, key=modes.get),
                        start_area=start_location.area,
                        end_area=component.location.area,
                        start_link=start_location.link,
                        end_link=component.location.link,
                        start_loc=start_location.loc,
                        end_loc=component.location.loc,
                        start_time=start_time,
                        end_time=component.start_time,
                        distance=distance,
                        purp=component.act,
                        attributes=attributes,
                    )
                    modes = {}
                    start_location = component.location
                    start_time = component.end_time
                    distance = 0
                    seq += 1

    def trip_legs(self, ignore: list[str] = ["pt interaction", "pt_interaction"]) -> Iterator[str]:
        """Yield plan trips as lists of legs. Trips are based on sequences of activity types used to separate
        legs within the same trip. The logic is based on the removal of public transit interaction activities.

        Args:
          ignore (list[str], optional): activities to remove. Defaults to ["pt interaction", "pt_interaction"].

        Yields:
            Iterator[str]

        """
        if self.day:
            legs = []
            for component in self[1:]:
                if isinstance(component, Leg):
                    legs.append(component)
                elif component.act not in ignore:
                    yield legs
                    legs = []

    @property
    def activity_classes(self) -> set:
        return set([a.act for a in self.activities])

    @property
    def mode_classes(self) -> set:
        return set([leg.mode for leg in self.legs])

    @property
    def closed(self) -> bool:
        """Check if plan starts and stops at the same facility (based on activity and location).

        Returns:
            bool:
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
        return self.first.lower() == "home"

    @property
    def length(self):
        return len(self.day)

    def __iter__(self):
        for component in self.day:
            yield component

    def get(self, idx, default=None):
        if -self.length <= idx < self.length:
            return self.day[idx]
        return default

    def plot(self, **kwargs):
        plot.plot_plan(self, **kwargs)

    def activity_tours(self):
        tours = []
        tour = []
        for act in self.activities:
            if act.act == "home":
                if tour:
                    tours.append(tour)
                tour = []
            else:
                tour.append(act)
        if tour:
            tours.append(tour)
        return tours

    def reversed(self):
        """Reverse iterate through plan, yield idx and component."""
        for i in range(self.length - 1, -1, -1):
            yield i, self[i]

    def __len__(self):
        return self.length

    def __getitem__(self, val):
        return self.day[val]

    def __eq__(self, other):
        if not isinstance(other, Plan):
            raise UserWarning(f"Cannot compare plan to non plan ({type(other)})")
        for i, j in zip(self, other):
            if not i == j:
                return False
        return True

    def __contains__(self, other):
        if not isinstance(other, PlanComponent):
            raise UserWarning(
                f"Expected PlanComponent type (either Leg or Activity) not ({type(other)})"
            )
        for c in self:
            if c == other:
                return True
        return False

    def add(self, p: Union[Activity, Leg, Trip, list[Activity, Leg, Trip]]) -> None:
        """Safely add a new component to the plan.

        Args:
          p (Union[Activity, Leg, Trip, list[Activity, Leg, Trip]]): component to add.

        """
        if isinstance(p, list):
            for c in p:
                self.add(c)

        elif isinstance(p, Activity):
            if self.day and isinstance(self.day[-1], Activity):  # enforce act-leg-act seq
                raise PAMSequenceValidationError(
                    "Failed to add to plan, next component must be a Trip or Leg."
                )
            self.day.append(p)

        elif isinstance(p, Leg) or isinstance(p, Trip):
            if not self.day:
                raise PAMSequenceValidationError(
                    "Failed to add to plan, first component must be Activity instance."
                )
            if not isinstance(self.day[-1], Activity):  # enforce act-leg-act seq
                raise PAMSequenceValidationError(
                    "Failed to add to plan, next component must be Activity instance."
                )
            self.day.append(p)

        else:
            raise UserWarning(f"Cannot add type: {type(p)} to plan.")

    # validation methods

    @property
    def valid_sequence(self) -> bool:
        """Check sequence of Activities and Legs.

        Returns:
            bool:

        """
        if not isinstance(self.day[0], Activity):
            return False

        for i, component in enumerate(self.day):
            if i % 2:  # uneven
                if not isinstance(component, Leg):
                    return False
            else:
                if not isinstance(component, Activity):
                    return False

        if not isinstance(self.day[-1], Activity):
            return False

        return True

    @property
    def valid_start_of_day_time(self) -> bool:
        """Check that start and end time of Activities and Legs are consistent.

        Returns:
            bool:

        """
        if not self.day[0].start_time == pam.variables.START_OF_DAY:
            return False
        return True

    @property
    def valid_time_sequence(self) -> bool:
        """Check that start and end time of Activities and Legs are consistent.

        Returns:
            bool:

        """
        for i in range(self.length - 1):
            if not self.day[i].end_time == self.day[i + 1].start_time:
                return False
        return True

    @property
    def valid_end_of_day_time(self) -> bool:
        """Check that start and end time of Activities and Legs are consistent.

        Returns:
            bool:

        """
        if not self.day[-1].end_time == pam.variables.END_OF_DAY:
            return False
        return True

    @property
    def valid_locations(self) -> bool:
        """Check that locations are consistent across Activities and Legs.

        Returns:
            bool:

        """
        for i in range(1, self.length):
            component = self.day[i]

            if isinstance(component, Activity):
                if not component.location == self.day[i - 1].end_location:
                    return False

            elif isinstance(component, Leg):
                if not component.start_location == self.day[i - 1].location:
                    return False

        return True

    @property
    def is_valid(self) -> bool:
        """Check for sequence, time and location structure and consistency.
        Note that this also checks that plan ends at END_OF_DAY.

        Returns:
            bool:

        """
        if self.valid_sequence and self.valid_time_sequence and self.valid_locations:
            return True
        else:
            return False

    def validate(self):
        self.validate_sequence()
        self.validate_times()
        self.validate_locations()
        return True

    def validate_sequence(self):
        if not self.valid_sequence:
            raise PAMSequenceValidationError()
        return True

    def validate_times(self):
        if not self.valid_time_sequence:
            raise PAMInvalidTimeSequenceError("Plan activity and trips times are not consistent")
        return True

    def validate_locations(self):
        if not self.valid_locations:
            raise PAMValidationLocationsError()
        return True

    def position_of(
        self, target: str = "home", search: Literal["first", "last"] = "last"
    ) -> Union[int, None]:
        """Return position of target activity type (either first or last depending on search).

        Args:
            target (str, optional): Defaults to "home".
            search (Literal['first', 'last'], optional): Defaults to "last".

        Returns:
            Union[int, None]: None if target activity type is not found.

        """
        if search == "last":
            last = None
            for seq, act in enumerate(self.day):
                if act.act.lower() == target:
                    last = seq
            return last

        if search == "first":
            for seq, act in enumerate(self.day):
                if act.act.lower() == target:
                    return seq

        raise UserWarning("Method only supports search types 'first' or 'last'.")

    # fixing methods

    def fix(self, crop=True, times=True, locations=True):
        if crop:
            self.crop()
        if times:
            self.fix_time_consistency()
        if locations:
            self.fix_location_consistency()

    def crop(self):
        """Crop a plan to end of day (END_OF_DAY). Plan components that start after this
        time are removed. Activities that end after this time are trimmed. If the last component
        is a Leg, this leg is removed and the previous activity extended.

        """
        # crop plan beyond end of day
        for idx, component in list(self.reversed()):
            if component.start_time > pam.variables.END_OF_DAY:
                self.logger.debug("Cropping plan components")
                self.day = self.day[:idx]
            else:
                break

        # crop plan that is out of sequence
        for idx in range(1, self.length):
            if self[idx].start_time < self[idx - 1].end_time:
                self.logger.debug("Cropping plan components")
                self.day = self.day[:idx]
                break
            if self[idx].start_time > self[idx].end_time:
                self.logger.debug("Cropping plan components")
                self.day = self.day[: idx + 1]
                break

        # deal with last component
        if isinstance(self.day[-1], Activity):
            self.day[-1].end_time = pam.variables.END_OF_DAY
        else:
            self.logger.debug("Cropping plan ending in Leg")
            self.day.pop(-1)
            self.day[-1].end_time = pam.variables.END_OF_DAY

    def fix_time_consistency(self):
        """Force plan component time consistency."""
        for i in range(self.length - 1):
            self.day[i + 1].start_time = self.day[i].end_time

    def fix_location_consistency(self):
        """Force plan locations consistency by adjusting leg locations."""
        for i in range(1, self.length - 1):
            component = self.day[i]

            if isinstance(component, Leg):
                component.start_location = copy(self.day[i - 1].location)
                component.end_location = copy(self.day[i + 1].location)

    def closed_duration(self, idx: int) -> datetime64:
        """Check duration of plan component at idx, if closed plan, combine first and last durations.

        Args:
          idx (int): index along plan component to check.

        Returns:
            datetime64:
        """
        if self.closed and (idx == 0 or idx == self.length - 1):
            return self.day[0].duration + self.day[-1].duration
        return self.day[idx].duration

    def infer_activity_idxs(self, target: Location, default: bool = True) -> set:
        """Infer idxs of home activity based on location.

        First pass looks to exclude other acts at home location, second pass adds home idxs.
        If a leg is found to start and end at the home location then the one with maximum duration is included.

        Args:
          target (Location):
          default (bool, optional): Defaults to True.

        Returns:
            set:
        """
        # todo untested for more than three possible home activities in a row.
        candidates = set()
        exclude = set()

        for idx, leg in enumerate(self.legs):
            prev_act_idx = 2 * idx
            next_act_idx = prev_act_idx + 2
            if leg.start_location == leg.end_location == target:  # check for larger duration
                if self.closed_duration(prev_act_idx) > self.closed_duration(next_act_idx):
                    exclude.add(next_act_idx)
                else:
                    exclude.add(prev_act_idx)

        for idx, act in enumerate(self.activities):
            if act.location == target and (idx * 2) not in exclude:
                candidates.add(idx * 2)

        if default and not candidates:  # assume first activity (and last if closed)
            if self.closed:
                return set([0, self.length - 1])
            return set([0])

        return candidates

    def infer_activities_from_tour_purpose(self) -> None:
        """Infer and set activity types based on trip purpose.

        Algorithm works like breadth first search,
        initiated from inferred home locations. Search takes place in two stages, first pass forward,
        the backward. The next activity type is set based on the trip purpose. Pass forward is exhausted
        first, because it's assumed that this is how the diary is originally filled in.

        """
        # find home activities
        home_idxs = self.infer_activity_idxs(target=self.home)
        for idx in home_idxs:
            self.day[idx].act = "home"

        area_map = {}
        remaining = set(range(0, self.length, 2)) - set(home_idxs)

        # forward traverse
        queue = [
            idx + 2 for idx in home_idxs if idx + 2 < self.length
        ]  # add next act idxs to queue\
        last_act = None

        while queue:  # traverse from home
            idx = queue.pop()

            if self.day[idx].act is None:
                act = self.day[idx - 1].purp.lower()
                location = str(self.day[idx].location.min)

                if act == last_act and location in area_map:
                    act = area_map[location]

                self.day[idx].act = act
                remaining -= {idx}
                last_act = act
                area_map[location] = act

                if idx + 2 in remaining:
                    queue.append(idx + 2)

        queue = []
        for location, activity in area_map.items():
            candidates = self.infer_activity_idxs(target=Location(area=location), default=False)
            for idx in candidates:
                if idx in remaining:
                    self.day[idx].act = activity
                    remaining -= {idx}
                    if idx + 2 in remaining:
                        queue.append(idx + 2)

        while queue:
            idx = queue.pop()

            if self.day[idx].act is None:
                act = self.day[idx - 1].purp.lower()
                location = self.day[idx].location.min

                if act == last_act and location in area_map:
                    act = area_map[location]

                self.day[idx].act = act
                remaining -= {idx}
                last_act = act
                area_map[location] = act

                if idx + 2 < self.length:
                    queue.append(idx + 2)

        # backward traverse
        queue = list(remaining)  # add next act idxs to queue

        while queue:  # traverse from home
            idx = queue.pop()

            if self.day[idx].act is None:
                act = self.day[idx + 1].purp.lower()
                location = self.day[idx].location.min

                if act == last_act and location in area_map:
                    act = area_map[location]

                self.day[idx].act = act
                remaining -= {idx}
                last_act = act
                area_map[location] = act

                if idx - 2 >= 0:
                    queue.append(idx - 2)

    def finalise_activity_end_times(self):
        """Add activity end times based on start time of next activity."""
        if len(self.day) > 1:
            for seq in range(0, len(self.day) - 1, 2):  # activities excluding last one
                self.day[seq].end_time = self.day[seq + 1].start_time
        self.day[-1].end_time = pam.variables.END_OF_DAY

    def set_leg_purposes(self) -> None:
        """Set leg purposes to destination activity.

        Skip 'pt interaction' activities.

        """
        for seq, component in enumerate(self):
            if isinstance(component, Leg):
                for j in range(seq + 1, len(self.day) - 1, 2):
                    act = self.day[j].act
                    if not act == "pt interaction":
                        self.day[seq].purp = act
                        break

    def autocomplete_matsim(self):
        """Complete leg start and end locations."""
        for seq, component in enumerate(self):
            if isinstance(component, Leg):
                self.day[seq].start_location = self.day[seq - 1].location
                self.day[seq].end_location = self.day[seq + 1].location

    def clear(self):
        self.day = []

    def print(self):
        for seq, component in enumerate(self):
            print(f"{seq}:\t{component}")

    def remove_activity(self, seq: int) -> tuple[Union[int, None], Union[int, None]]:
        """Remove an activity from plan at given seq.

        Does not remove adjacent legs.
        Will also check if an activity is wrapped and remove accordingly. Returns

        Args:
          seq (int):

        Returns:
          tuple[Union[int, None], Union[int, None]]:
            (adjusted) idx of previous (p_idx) and subsequent (s_idx) activities as a tuple.
            If there is no previous or subsequent activity, ie a removed activity is at the start or end of an open plan, then None can be returned.
            If all activities are removed then None, None is returned.

        """
        assert isinstance(self.day[seq], Activity)

        if seq == 0 and seq == self.length - 1:  # remove activity that is entire plan
            self.logger.debug(
                f" remove_activity, idx:{seq} type:{self.day[seq].act}, plan now empty"
            )
            self.day.pop(0)
            return None, None

        if (seq == 0 or seq == self.length - 1) and self.closed:  # remove activity that wraps
            self.logger.debug(f" remove_activity, idx:{seq} type:{self.day[seq].act}, wraps")
            self.day.pop(0)
            self.day.pop(self.length - 1)
            if self.length == 1:  # all activities have been removed
                self.logger.debug(
                    f" remove_activity, idx:{seq} type:{self.day[seq].act}, now empty"
                )
                return None, None
            return self.length - 2, 1

        if seq == 0:  # remove first activity
            self.logger.debug(
                f" remove_activity, idx:{seq} type:{self.day[seq].act}, first activity"
            )
            self.day.pop(seq)
            return None, 1

        if seq == self.length - 1:  # remove last activity
            self.logger.debug(
                f" remove_activity, idx:{seq} type:{self.day[seq].act}, last activity"
            )
            self.day.pop(seq)
            return self.length - 2, None

        else:  # remove activity somewhere in middle of plan
            self.logger.debug(f" remove_activity, idx:{seq} type:{self.day[seq].act}")
            self.day.pop(seq)
            return seq - 2, seq + 1

    def move_activity(
        self, seq: int, default: Union[Literal["home"], Location] = "home", new_mode: str = "walk"
    ) -> None:
        """Changes Activity location and associated journeys

        Args:
          seq (int):
          default (Union[Literal["home"], Location], optional): Defaults to "home".
          new_mode (str, optional): access/egress journey switching to this mode. Ie 'walk'. Defaults to "walk".

        """
        assert isinstance(self.day[seq], Activity)

        # decide on the new location
        if default == "home":
            new_location = self.home
        else:
            assert isinstance(default, Location)
            new_location = default

        # actually update the location
        self.day[seq].location = new_location
        if seq != 0:
            # if it's not the first activity of plan
            # update leg that leads to activity at seq
            self.day[seq - 1].end_location = new_location
            self.mode_shift(seq - 1, new_mode)
        if seq != len(self.day) - 1:
            # if it's not the last activity of plan
            # update leg that leads to activity at seq
            self.day[seq + 1].start_location = new_location
            self.mode_shift(seq + 1, new_mode)

    def fill_plan(
        self, idx_start: Union[int, None], idx_end: Union[int, None], default: Any = "home"
    ) -> True:
        """Fill a plan after Activity has been removed.

        Plan is filled between given remaining
        activity locations (idx_start and idx_end). Note that the plan will also have legs that
        need to be removed.

        Args:
          idx_start (Union[int, None]): location of previous Activity.
          idx_end (Union[int, None]): location of subsequent Activity.
          default (Any, optional): Not Used. Defaults to "home".

        Returns:
          True:

        """
        self.logger.debug(f" fill_plan, {idx_start}->{idx_end}")

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
            if self.position_of(target="home") is None:
                raise ValueError("Require home activity")
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

            pivot_idx = self.position_of(target="home")
            if pivot_idx is None:
                self.logger.warning("Unable to find home activity, changing plan to stay at home")
                self.stay_at_home()
                return True

            self.expand(pivot_idx)
            return True

        # need to change first leg for new destination
        self.join_activities(idx_start, idx_end)
        return True

    def expand(self, pivot_idx: int) -> None:
        """Fill plan by expanding a pivot activity.

        Args:
          pivot_idx (int):

        """
        # todo this isn't great - just pushes other activities to edges of day

        new_time = pam.utils.minutes_to_datetime(0)
        for seq in range(pivot_idx + 1):  # push forward pivot and all proceeding components
            new_time = self.day[seq].shift_start_time(new_time)

        new_time = pam.variables.END_OF_DAY
        for seq in range(self.length - 1, pivot_idx, -1):  # push back all subsequent components
            new_time = self.day[seq].shift_end_time(new_time)

        self.day[pivot_idx].end_time = new_time  # expand pivot

    def join_activities(self, idx_start: int, idx_end: int) -> None:
        """Join together two Activities with new Leg, expand last home activity.

        Args:
          idx_start (int):
          idx_end (int):

        """
        self.day[idx_start + 1].end_location = self.day[idx_end - 1].end_location
        self.day[idx_start + 1].purp = self.day[idx_end - 1].purp
        self.day.pop(idx_end - 1)  # remove second leg

        # todo add logic to change mode and time of leg

        # press plans away from pivoting activity
        pivot_idx = self.position_of(target="home")
        if pivot_idx is None:
            self.logger.warning("Unable to find home activity, changing plan to stay at home")
            self.stay_at_home()
            return None

        self.expand(pivot_idx)

    def combine_matching_activities(self, idx_start: int, idx_end: int) -> None:
        """Combine two given activities into same activity, remove surplus Legs

        Args:
          idx_start (int):
          idx_end (int):

        """
        self.day[idx_start].end_time = self.day[idx_end].end_time  # extend proceeding act
        self.day.pop(idx_end)  # remove subsequent activity
        self.day.pop(idx_end - 1)  # remove subsequent leg
        self.day.pop(idx_start + 1)  # remove proceeding leg

    def combine_wrapped_activities(self, idx_start: int, idx_end: int) -> None:
        """Combine two given activities that will wrap around day, remove surplus Legs

        Args:
          idx_start (int):
          idx_end (int):

        """
        # extend proceeding act to end of day
        self.day[idx_start].end_time = pam.variables.END_OF_DAY
        # extend subsequent act to start of day
        self.day[idx_end].start_time = pam.utils.minutes_to_datetime(0)
        self.day.pop(idx_start + 1)  # remove proceeding leg
        self.day.pop(idx_end - 1)  # remove subsequent leg

    def stay_at_home(self):
        self.logger.debug(f" stay_at_home, location:{self.home}")
        self.day = [
            Activity(
                seq=1,
                act="home",
                area=self.home.area,
                start_time=pam.utils.minutes_to_datetime(0),
                end_time=pam.variables.END_OF_DAY,
            )
        ]

    def get_home_duration(self):
        """Get the total duration of home activities."""
        # total time spent at home
        home_duration = timedelta(0)
        for plan in self.day:
            if plan.act == "home":
                home_duration += plan.duration

        return home_duration

    def mode_shift(
        self,
        seq: int,
        new_mode="walk",
        mode_speed={"car": 37, "bus": 10, "walk": 4, "cycle": 14, "pt": 23, "rail": 37},
        update_duration=False,
    ) -> None:
        """Changes mode for a leg, along with any legs in the same tour.

        Leg durations are adjusted to mode speed, and home activity durations revisited to fit within the 24-hr plan.
        Default speed values are from National Travel Survey data (NTS0303).

        Args:
          seq (int): leg index in self.day
          new_mode (string, optional): default mode shift. Defaults to "walk".
          mode_speed (dict, optional): a dictionary of average mode speeds (kph). Defaults to {"car": 37, "bus": 10, "walk": 4, "cycle": 14, "pt": 23, "rail": 37}.
          update_duration (bool, optional): whether to update leg durations based on mode speed. Defaults to False.

        """
        assert isinstance(self.day[seq], Leg)

        tour = self.get_leg_tour(seq)
        for seq, plan in enumerate(self.day):
            if isinstance(plan, Leg):
                act_from = self.day[seq - 1]
                act_to = self.day[seq + 1]
                for other_act in tour:
                    # if any of the trip ends belongs in the tour change the mode
                    if act_from.is_exact(other_act) or act_to.is_exact(other_act):
                        if update_duration:
                            shift_duration = (
                                (mode_speed[plan.mode] / mode_speed[new_mode]) * plan.duration
                            ) - plan.duration  # calculate any trip duration changes due to mode shift
                        plan.mode = new_mode  # change mode
                        if update_duration:
                            self.change_duration(
                                seq=seq, shift_duration=shift_duration
                            )  # change the duration of the trip

        if update_duration:
            # adjust home activities time in order fit revised legs/activities within a 24hr day
            home_duration = self.get_home_duration()
            home_duration_factor = (
                self.day[-1].end_time - END_OF_DAY
            ) / home_duration  # factor to adjust home activity time by

            for seq, plan in enumerate(self.day):
                if plan.act == "home":
                    shift_duration = -home_duration_factor * plan.duration
                    shift_duration = timedelta(
                        seconds=round(shift_duration / timedelta(seconds=1))
                    )  # round to second
                    self.change_duration(seq=seq, shift_duration=shift_duration)

            # make sure the last activity ends in the end of day (ie remove potential rounding errors)
            if self.day[-1].end_time != END_OF_DAY:
                self.day[-1].end_time = END_OF_DAY

    def change_duration(self, seq: int, shift_duration: timedelta) -> None:
        """Change the duration of a leg and shift subsequent activities/legs forward.

        Args:
            seq (int): leg index in self.day.
            shift_duration (timedelta): the number of seconds to change the leg duration by.

        """
        # change leg duration
        self.day[seq].end_time = self.day[seq].end_time + shift_duration

        # shift all subsequent legs and activities
        for idx in range(seq + 1, len(self.day)):
            start_time = self.day[idx].start_time
            self.day[idx].shift_start_time(start_time + shift_duration)

    def get_leg_tour(self, seq: int) -> list:
        """Get the tour of a leg

        Args:
          seq (int): plan sequence. Must be a leg sequence.

        Returns:
          list: activities in a tour.

        """
        assert isinstance(self.day[seq], Leg)

        act_from = self.day[seq - 1]
        act_to = self.day[seq + 1]

        for tour in self.activity_tours():
            for tour_act in tour:
                if act_from.is_exact(tour_act) or act_to.is_exact(tour_act):
                    return tour


class PlanComponent:
    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def hours(self):
        return pam.utils.timedelta_to_hours(self.end_time - self.start_time)

    def shift_start_time(self, new_start_time: datetime64) -> datetime64:
        """Given a new start time, set start time & end time based on previous duration.

        Args:
            new_start_time (datetime64):

        Returns:
            datetime64: new end time

        """
        duration = self.duration
        self.start_time = new_start_time
        self.end_time = new_start_time + duration
        return self.end_time

    def shift_end_time(self, new_end_time: datetime64) -> datetime64:
        """Given a new end time, set end time & start time based on previous duration.

        Args:
          new_end_time (datetime64):

        Returns:
          datetime64: new start time.

        """
        duration = self.duration
        self.end_time = new_end_time
        self.start_time = new_end_time - duration
        return self.start_time

    def shift_duration(
        self, new_duration: timedelta, new_start_time: Optional[datetime64] = None
    ) -> datetime64:
        """Given a new duration and optionally start time, set start time & set end time based on duration.

        Args:
          new_duration (timedelta):
          new_start_time (datetime64, optional): Defaults to None.

        Returns:
          datetime64: new end time.

        """
        if new_start_time is not None:
            self.start_time = new_start_time
        self.end_time = self.start_time + new_duration
        return self.end_time


class Activity(PlanComponent):
    def __init__(
        self,
        seq=None,
        act=None,
        area=None,
        link=None,
        loc=None,
        start_time=None,
        end_time=None,
        freq=None,
    ):
        self.seq = seq
        self.act = act
        self.location = Location(loc=loc, link=link, area=area)
        self.start_time = start_time
        self.end_time = end_time
        self.freq = freq

    def __str__(self):
        return (
            f"Activity(act:{self.act}, location:{self.location}, "
            f"time:{self.start_time.time()} --> {self.end_time.time()}, "
            f"duration:{self.duration})"
        )

    def __eq__(self, other):
        """Check for equality with activity type and location. Ignoring times and duration."""
        return (self.location == other.location) and (self.act == other.act)

    def is_exact(self, other):
        return (
            (self.location == other.location)
            and (self.act == other.act)
            and (self.start_time == other.start_time)
            and (self.end_time == other.end_time)
        )

    def isin_exact(self, activities: list):
        for other in activities:
            if self.is_exact(other):
                return True
        return False

    def validate_matsim(self) -> None:
        """Checks if activity has required fields for a valid matsim plan."""
        if self.act is None:
            raise InvalidMATSimError("Activity requires a type.")
        if self.start_time is None and self.end_time is None:
            raise InvalidMATSimError("Activity requires either start time or end_time.")
        if self.location.loc is None and self.location.link is None:
            raise InvalidMATSimError("Activity requires link id or x,y coordinates.")


class Leg(PlanComponent):
    act = "travel"

    def __init__(
        self,
        seq=None,
        mode=None,
        start_area=None,
        end_area=None,
        start_link=None,
        end_link=None,
        start_loc=None,
        end_loc=None,
        start_time=None,
        end_time=None,
        distance=None,
        purp=None,
        freq=None,
        attributes={},
        route=None,
    ):
        self.seq = seq
        self.purp = purp
        self.mode = mode
        self.start_location = Location(loc=start_loc, link=start_link, area=start_area)
        self.end_location = Location(loc=end_loc, link=end_link, area=end_area)
        self.start_time = start_time
        self.end_time = end_time
        self.freq = freq
        self._distance = distance
        # relevant for simulated plans
        self.attributes = attributes
        if route is not None:
            self.route = route
        else:
            self.route = Route()

    def __str__(self):
        return (
            f"Leg(mode:{self.mode}, area:{self.start_location} --> "
            f"{self.end_location}, time:{self.start_time.time()} --> {self.end_time.time()}, "
            f"duration:{self.duration})"
        )

    def __eq__(self, other):
        return (
            self.start_location == other.start_location
            and self.end_location == other.end_location
            and self.mode == other.mode
            and self.start_time == other.start_time
            and self.end_time == other.end_time
        )

    @property
    def distance(self):
        """Distance, assumed to be in m in either case."""
        if self._distance is not None:
            return self._distance
        return self.euclidean_distance * 1000

    @property
    def euclidean_distance(self):
        # calculate leg euclidean distance in km:
        # todo prefer this be in m, not km, (see above) but unsure of implications elsewhere
        # assumes grid definition of Location class
        return (
            (self.end_location.loc.x - self.start_location.loc.x) ** 2
            + (self.end_location.loc.y - self.start_location.loc.y) ** 2
        ) ** 0.5 / 1000

    @property
    def service_id(self):
        return self.route.transit.get("service_id")

    @property
    def route_id(self):
        return self.route.transit.get("route_id")

    @property
    def o_stop(self):
        return self.route.transit.get("o_stop")

    @property
    def d_stop(self):
        return self.route.transit.get("d_stop")

    @property
    def boarding_time(self):
        time = self.route.transit.get("boardingTime")
        if time is not None:
            return utils.matsim_time_to_datetime(time)
        return None

    @property
    def network_route(self):
        return self.route.network_route


class Route:
    """xml element wrapper for leg routes, in the simplest case of a leg with no route, this will behave as an empty dictionary.
    For routed legs this provides some convenience properties such as is_transit, and transit_route.
    """

    def __init__(self, xml_elem=None) -> None:
        if xml_elem:
            self.xml = xml_elem[0]
        else:
            self.xml = {}  # this allows an empty route to behave as an empty dict

    @property
    def exists(self) -> bool:
        return not isinstance(self.xml, dict)

    @property
    def type(self):
        return self.xml.get("type", None)

    @property
    def is_transit(self) -> bool:
        return self.type == "default_pt"

    @property
    def is_routed(self) -> bool:
        return self.type == "links"

    @property
    def is_teleported(self) -> bool:
        return self.type == "generic"

    @property
    def network_route(self) -> list:
        if self.is_routed:
            return self.xml.text.split(" ")
        return []

    @property
    def transit(self) -> dict:
        if self.is_transit:
            return json.loads(self.xml.text.strip())
        return {}

    def get(self, key, default=None) -> str:
        return self.xml.get(key, default)

    def __getitem__(self, key):
        return self.xml[key]

    @property
    def distance(self) -> float:
        distance = self.get("distance")
        if distance is not None:
            return float(distance)
        return None


class RouteV11(Route):
    def __init__(self, xml_elem) -> None:
        super().__init__(xml_elem)

    @property
    def is_transit(self) -> bool:
        return self.type == "experimentalPt1"

    @property
    def transit(self) -> dict:
        if self.is_transit:
            pt_details = self.xml.text.split("===")
            return {
                "accessFacilityId": pt_details[1],
                "transitLineId": pt_details[2],
                "transitRouteId": pt_details[3],
                "egressFacilityId": pt_details[4],
            }
        return {}


class Trip(Leg):
    pass
