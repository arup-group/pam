import random
from typing import Any, Optional


def bin_integer_transformer(features, target, bins, default=None):
    """Bin a target integer feature based on bins.

    Where bins are a dict, with keys as a tuple of bin extends (inclusive) and values as the new mapping.
    Missing ranges will return None.
    Where features are a dictionary structure of features, eg: {'age':1, ...}.
    """
    value = features.get(target)
    if value is None:
        raise KeyError(f"Can not find target key: {target} in sampling features: {features}")
    for (lower, upper), new_value in bins.items():
        if lower < int(value) <= upper:
            return new_value
    return default


def discrete_joint_distribution_sampler(
    features: dict,
    mapping: Any,
    distribution: dict[dict],
    careful: bool = False,
    seed: Optional[int] = None,
) -> bool:
    """Randomly sample from a joint distribution based some discrete features.

    Args:
        features (dict): a dictionary structure of features, eg: {'gender':'female'}
        mapping (Any): the feature name for each level of the distribution, e.g.: ['age', 'gender']
        distribution (dict[dict]):
            A nested dict of probabilities based on possible features.
            E.g.: {'0-0': {'male': 0, 'female': 0},... , '90-120': {'male': 1, 'female': .5}}
        careful (bool, optional):
            If True, missing mapped feature in `distribution` will raise an exception. If False, missing values will return False.
            Defaults to False.
        seed (Optional[int], optional): If given, seed number for reproducible results. Defaults to None.

    Raises:
        KeyError: all `mapping` keys must be in `features`.
        KeyError: If `careful`, mapped feature must be a key in `distribution`.

    Returns:
        bool:
    """

    # Fix random seed
    random.seed(seed)
    p = distribution
    for key in mapping:
        value = features.get(key)
        if value is None:
            raise KeyError(f"Can not find mapping: {key} in sampling features: {features}")

        p = p.get(value)
        if p is None:
            if careful:
                raise KeyError(f"Can not find feature for {key}: {value} in distribution: {p}")
            else:
                return False
    return random.random() <= p
