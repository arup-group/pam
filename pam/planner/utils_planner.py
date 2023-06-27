import random
from typing import List, Union

import numpy as np

from pam.activity import Activity, Leg, Plan


def calculate_mnl_probabilities(x: Union[np.array, List]) -> np.array:
    """Calculates MNL probabilities from a set of alternatives."""
    return np.exp(x) / np.exp(x).sum()


def sample_weighted(weights: np.array) -> int:
    """Weighted sampling.
    Returns the index of the selection.
    """
    return random.choices(range(len(weights)), weights=weights, k=1)[0]


def get_trip_chains(plan: Plan, act: str = "home") -> List[List[Union[Activity, Leg]]]:
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


def apply_mode_to_home_chain(act: Activity, trmode: str):
    """Apply a transport mode across a home-based trip chain,
    which comprises the specified activity.

    :param act: The activity that is part of the trip chain.
    :param trmode: The mode to apply to each leg of the chain.
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
