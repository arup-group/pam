from random import randrange
from datetime import timedelta
from copy import deepcopy

from pam.core import Population, Person, Household
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.utils import td_to_s, minutes_to_timedelta
from pam.variables import END_OF_DAY


def apply_jitter_to_plan(
    plan: Plan,
    jitter: timedelta,
    min_duration: timedelta
    ):
    """
    Apply time jitter to activity durations in a plan, leg durations are kept the same.
    Activity durations are jittered in sequence order. At each step the activity
    is jittered according to the maximum jitter and minimum duration of all activities
    in the plan.
    Args:
        plan (Plan): plan to be jittered
        jitter (timedelta): maximum jitter
        min_duration (timedelta): minimum activity duration
    """
    if plan.length == 1:  # do nothing
        return None
    for i in range(0, plan.length-1, 2):
        jitter_activity(plan, i, jitter=jitter, min_duration=min_duration)


def jitter_activity(
    plan: Plan,
    i: int,
    jitter: timedelta,
    min_duration: timedelta
    ):
    """
    Jitter duration of given activity at index i. Remaining activities and legs after activity are also shifted.
    Leg durations are not changed.
    Subsequent activity durations are equally change to maintain 24hr plan.
    """
    act = plan[i]
    if not isinstance(act, Activity):
        raise UserWarning(f"Expected type of Activity for act, not {type(act)}")

    prev_duration = act.duration
    tail = (len(plan) - i)/2

    min_start = max(act.start_time + min_duration, act.end_time - jitter)

    allowance = plan[-1].end_time - act.end_time
    for j in range(i+1, len(plan), 2):  # legs
        allowance =- plan[j].duration
    for j in range(i+2, len(plan)+1, 2):  # acts
        allowance =- min_duration

    max_end = min(plan[-1].end_time - allowance, act.end_time + jitter)
    duration = (max_end - min_start).seconds

    new_duration = timedelta(seconds=randrange(duration))
    change = (new_duration - prev_duration)/tail

    time = act.shift_duration(new_duration)
    time = plan[i+1].shift_start_time(time)  # shift first tail leg

    for j in range(i+2, len(plan)-1, 2):  # tail acts
        time = plan[j].shift_start_time(time)
        time = plan[j].shift_duration(plan[j].duration-change)
        time = plan[j+1].shift_start_time(time)  # leg

    # final act
    time = plan[-1].shift_start_time(time)
    plan[-1].end_time = END_OF_DAY

