import numpy as np

from pam.activity import Plan
from pam.utils import td_to_s


def plan_to_one_hot(
    plan: Plan,
    mapping:dict,
    bin_size:int=3600,
    duration:int=86400
    ) -> np.array:
    """
    Transform a pam.activity.Plan into a one-hot encoded array. Output array is two dimensional.
    First axis represents time, binnned according to bin_size given in seconds.
    Seconds axis is a one-hot endcoding of activity type based on the given mapping. Note that Leg
    components will have the encoding "travel" which should be included in the mapping. Location and
    mode information is lost. Some plan components may be lost if their durations are less than
    the chosen bin six. Plan components beyond 24 hours are cropped.

    Args:
        plan (Plan): input Plan object to be encoded as one-hot
        mapping (dict): dictionary mapping of activity types to one-hot index, eg {"home":0, "travel":1}
        bin_size (int, optional): time bin size (in seconds). Defaults to 3600.
        duration (int, optional): day_duration (in seconds). Defaults to 86400.

    Returns:
        np.array: one-hot encoded plan
    """
    bins = int(duration / bin_size)
    encoded = np.zeros((bins,len(mapping)))

    start_bin = 0
    reference_time = plan.day[0].start_time
    for component in plan.day:
        index = mapping.get(component.act, None)
        end_bin = round(td_to_s(component.end_time - reference_time) / bin_size)

        if end_bin >= duration:  # deal with last component
            end_bin = duration
            encoded[start_bin:end_bin, index] = 1.0
            break

        encoded[start_bin:end_bin, index] = 1.0
        start_bin = end_bin

    return encoded


def plan_to_categorical(
    plan: Plan,
    mapping: dict,
    bin_size:int=3600,
    duration:int=86400
    ) -> np.array:
    """
    Transform a pam.activity.Plan into a categorical integer array, eg: [0,0,0,1,1,2,0].
    Axis represents time, binnned according to bin_size given in seconds.
    A mapping dictionary should be provided, such that it can be persistent between multiple calls for
    new plans.
    Note that Leg components will have the encoding "travel" which will be included in the mapping. Location and
    mode information is lost. Some plan components may be lost if their durations are less than
    the chosen bin six. Plan components beyond 24 hours are cropped.

    Args:
        plan (Plan): input Plan object to be encoded as one-hot
        mapping (dict): persistent dictionary mapping of activity types
        bin_size (int, optional): time bin size (in seconds). Defaults to 3600.
        duration (int, optional): day_duration (in seconds). Defaults to 86400.

    Returns:
        np.array: encoded plan
    """
    bins = int(duration / bin_size)
    encoded = np.zeros((bins))

    start_bin = 0
    reference_time = plan.day[0].start_time
    for component in plan.day:
        act = component.act
        if act not in mapping:
            mapping[act] = len(mapping)
        index = mapping[act]
        end_bin = round(td_to_s(component.end_time - reference_time) / bin_size)

        if end_bin >= duration:  # deal with last component
            end_bin = duration
            encoded[start_bin:end_bin] = index
            break

        encoded[start_bin:end_bin] = index
        start_bin = end_bin

    return encoded

