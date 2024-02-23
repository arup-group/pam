import datetime
import random
from copy import deepcopy
from typing import Union

import numpy as np

from pam.activity import Activity, Leg, Plan
from pam.variables import LONG_TERM_ACTIVITIES


def calculate_mnl_probabilities(x: Union[np.array, list]) -> np.array:
    """Calculates MNL probabilities from a set of alternatives."""
    return np.exp(x) / np.exp(x).sum()


def sample_weighted(weights: np.array) -> int:
    """Weighted sampling.
    Returns the index of the selection.
    """
    return random.choices(range(len(weights)), weights=weights, k=1)[0]


def get_trip_chains(plan: Plan, act: str = "home") -> list[list[Union[Activity, Leg]]]:
    """Get trip chains starting and/or ending at a long-term activity."""
    chains = []
    chain = []
    for elem in plan.day:
        if isinstance(elem, Activity) and elem.act == act:
            if len(chain) > 0:
                chains.append(chain + [elem])
                chain = []
        chain.append(elem)

    if len(chain) > 1:
        chains += [chain]  # add any remaining trips until the end of the day

    return chains


def get_trip_chains_either_anchor(
    plan: Plan, acts: list[str] = LONG_TERM_ACTIVITIES
) -> list[list[Union[Activity, Leg]]]:
    """Get trip chains starting and/OR ending at a long-term activity.
    Similar to get_trip_chains, but can slice plans on multiple activity types.
    """
    chains = []
    chain = []
    for elem in plan.day:
        if isinstance(elem, Activity) and elem.act in acts:
            if len(chain) > 0:
                chains.append(chain + [elem])
                chain = []
        chain.append(elem)

    if len(chain) > 1:
        chains += [chain]  # add any remaining trips until the end of the day

    return chains


def apply_mode_to_home_chain(act: Activity, trmode: str) -> None:
    """Apply a transport mode across a home-based trip chain,
    which comprises the specified activity.

    Args:
        act (Activity): The activity that is part of the trip chain.
        trmode (str): The mode to apply to each leg of the chain.
    """
    if "next" not in act.__dict__:
        raise KeyError(
            "Plan is not linked. Please use `pam.operations.cropping.link_plan` to link activities and legs."
        )

    # apply forwards
    elem = act.next
    while (elem is not None) and (elem.act != "home"):
        if isinstance(elem, Leg):
            elem.mode = trmode
        elem = elem.next

    # apply backwards
    elem = act.previous
    while (elem is not None) and (elem.act != "home"):
        if isinstance(elem, Leg):
            elem.mode = trmode
        elem = elem.previous


def get_validate(obj, name: str):
    """Get an object's attribute, or raise an error if its value is None."""
    attr = getattr(obj, name)
    if attr is None:
        raise ValueError(f"Attribute {name} has not been set yet")
    return attr


def get_act_names(seqs: list[Union[Activity, Leg]]) -> list[str]:
    """
    Get the activity names of a plan.

    Args:
        seqs: a list of plan components (activities and legs)

    Returns:
        list: a list of the activity names
    """
    return [x.act for x in seqs if isinstance(x, Activity)]


def get_first_leg_time_ratio(chain: list[Union[Activity, Leg]]) -> float:
    """Get the ratio of the first leg duration to the total trip chain duration.

    Args:
        chain: a chain of activity and legs between two long-term activities

    Returns:
        float: the first leg duration ratio

    """
    durations = [x.duration / datetime.timedelta(seconds=1) for x in chain if isinstance(x, Leg)]
    ratio = durations[0] / sum(durations)

    return ratio


def convert_single_anchor_roundtrip(chain: list[Union[Activity, Leg]]) -> None:
    """If a trip chain only has one anchor, make it a round-trip.
    - If only the start activity is an anchor, it appends a return trip to the start location.
    - If only the end activity is an anchor, it inserts a first leg from the end activity location.
    - If neither end is an anchor, it treats the first location as an anchor.
    The addition of the "return" elements is done in-place.

    Args:
        chain: a chain of activity and legs between two long-term activities

    Returns:
        None
    """
    if chain[0].act not in LONG_TERM_ACTIVITIES and chain[-1].act in LONG_TERM_ACTIVITIES:
        leg = deepcopy(chain[-2])
        act = deepcopy(chain[-1])
        leg.start_location = act.location
        chain.insert(0, leg)
        chain.insert(0, act)
    elif chain[-1].act not in LONG_TERM_ACTIVITIES and chain[0].act in LONG_TERM_ACTIVITIES:
        leg = deepcopy(chain[1])
        act = deepcopy(chain[0])
        chain.append(leg)
        chain.append(act)
    # if all activities are non-disrectionary, create a tour from/to the first location
    elif chain[-1].act not in LONG_TERM_ACTIVITIES and chain[0].act not in LONG_TERM_ACTIVITIES:
        act = deepcopy(chain[0])
        leg = deepcopy(chain[1])
        act.act = "home"
        leg.start_location = act.location
        chain.insert(0, leg)
        chain.insert(0, act)
        chain.append(leg)
        chain.append(act)


def safe_divide(x: np.array, y: np.array) -> np.array:
    """Safely divide two arrays. When dividing by zero, the result is set to zero.


    Args:
        x (np.array): Numerator array.
        y (np.array): Denominator array.

    Returns:
        np.array: Divided array.
    """
    return np.divide(x, y, out=np.zeros(x.shape, dtype=np.float64), where=y != 0)
