import random


def bin_integer_transformer(features, target, bins, default=None):
    """Bin a target integer feature based on bins. Where bins are a dict, with keys as
    a tuple of bin extends (inclusive) and values as the new mapping. Missing ranges
    will return None.
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
    features, mapping, distribution, careful=False, seed: int = None
):
    """Randomly sample from a joint distribution based some discrete features.

    Where features are a dictionary structure of features, eg: {'gender':'female'}

    Distribution is a nested dict of probabilities based on possible features, eg:
    {'0-0': {'male': 0, 'female': 0},... , '90-120': {'male': 1, 'female': .5}}

    Mapping provides the feature name for each level of the distribution, eg:
    ['age', 'gender']

    Missing keys return False, unless careful is set to True, which will raise an error.

    :params int seed: seed number for reproducible results (None default - does not fix seed)
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
