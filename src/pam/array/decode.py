from datetime import datetime, timedelta

import numpy as np

from pam.activity import Activity, Leg, Plan
from pam.variables import END_OF_DAY, START_OF_DAY


def one_hot_to_plan(
    array: np.array,
    mapping: dict,
    bin_size: int = 3600,
    duration: int = 86400,
    start_of_day: datetime = START_OF_DAY,
    end_of_day: datetime = END_OF_DAY,
    leg_encoding: str = "travel",
    default_leg_mode: str = "car",
    default_activity: str = "other",
) -> Plan:
    """Decode a one-hot encoded plan array for a given mapping. Attempts to create a valid plan sequence
    by assuming obviously missing components. Does not support locations, these must be created
    manually.

    Args:
        array (np.array): input one-hot encoded plan.
        mapping (dict): encoding index to activity, eg {0: 'home', 1:'travel'}.
        bin_size (int, optional): in seconds. Defaults to 3600.
        duration (int, optional): in seconds. Defaults to 86400.
        start_of_day (datetime, optional): start datetime of first activity. Defaults to START_OF_DAY.
        end_of_day (datetime, optional): end time of last activity. Defaults to END_OF_DAY.
        leg_encoding (str, optional): activity encoding for travel components. Defaults to "travel".
        default_leg_mode (str, optional): assumed leg mode when unknown. Defaults to "car".
        default_activity (str, optional): assumed activity when unknown. Defaults to "other".

    Raises:
        UserWarning: may raise a UserWarning if bin_size and duration are not consistent with array size.

    Returns:
        Plan: pam.activity.Plan
    """
    bins = int(duration / bin_size)
    if not len(array) == bins:
        raise UserWarning(
            "Specified plan duration and bin lengths do not match given array length."
        )

    proposed_plan = []
    for act, start_time in iter_array(
        array=array, mapping=mapping, start_of_day=start_of_day, bin_size=bin_size
    ):
        if act == leg_encoding:  # add leg
            proposed_plan.append(Leg(mode=default_leg_mode, start_time=start_time))
        else:
            proposed_plan.append(Activity(act=act, start_time=start_time))

    add_end_times(proposed_plan, end_of_day)
    fix_missing_start_activity(proposed_plan, start_of_day, bin_size)
    fix_missing_end_activity(proposed_plan, end_of_day, bin_size)
    fix_missing_components(proposed_plan, default_leg_mode, default_activity)

    plan = Plan()
    plan.day = proposed_plan
    return plan


def iter_array(array, mapping, start_of_day=START_OF_DAY, bin_size=3600):
    prev = None
    for i, time_bin in enumerate(array):
        if (prev is None) or (not np.array_equal(time_bin, prev)):  # new component class
            component_class = mapping.get(np.argmax(time_bin))
            if component_class is None:
                raise UserWarning(
                    f"Not found index of {np.argmax(time_bin)} in supplied mapping: {mapping}."
                )
            yield component_class, start_of_day + timedelta(seconds=(i * bin_size))
        prev = time_bin


def add_end_times(plan: list, end_of_day=END_OF_DAY):
    # add end_times
    for i in range(len(plan) - 1):
        plan[i].end_time = plan[i + 1].start_time
    plan[-1].end_time = end_of_day


def fix_missing_start_activity(plan: list, start_of_day=START_OF_DAY, bin_size=3600):
    if not isinstance(plan[0], Activity):
        end_time = start_of_day + timedelta(seconds=int(bin_size / 2))  # expected duration
        plan.insert(
            0, Activity(act="home", start_time=start_of_day, end_time=end_time)
        )  # sensible assumption
        plan[1].start_time = end_time


def fix_missing_end_activity(plan: list, end_of_day=END_OF_DAY, bin_size=3600):
    if not isinstance(plan[-1], Activity):
        start_time = end_of_day - timedelta(seconds=int(bin_size / 2))  # expected duration
        plan.append(
            Activity(act="home", start_time=start_time, end_time=end_of_day)
        )  # sensible assumption
        plan[-2].end_time = start_time


def fix_missing_components(
    plan: list, bin_size=3600, default_leg_mode="car", default_activity="other"
):
    for i in range(len(plan) - 1):
        if isinstance(plan[i], type(plan[i + 1])):
            start_time = plan[i].end_time - timedelta(seconds=int(bin_size / 4))
            end_time = plan[i].end_time + timedelta(seconds=int(bin_size / 4))

            if isinstance(plan[i], Activity):  # add missing Leg
                plan.insert(
                    i + 1, Leg(mode=default_leg_mode, start_time=start_time, end_time=end_time)
                )
                plan[i].end_time = start_time
                plan[i + 2].start_time = end_time

            if isinstance(plan[i], Leg):  # add missing Activity
                plan.insert(
                    i + 1, Activity(act=default_activity, start_time=start_time, end_time=end_time)
                )
                plan[i].end_time = start_time
                plan[i + 2].start_time = end_time
