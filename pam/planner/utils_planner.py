import numpy as np
import random
from typing import Union, List


def calculate_mnl_probabilities(x: Union[np.array, List]) -> np.array:
    """
    Calculates MNL probabilities from a set of alternatives.
    """
    return np.exp(x)/np.exp(x).sum()


def sample_weighted(weights: np.array) -> int:
    """
    Weighted sampling. 
    Returns the index of the selection.
    """
    return random.choices(range(len(weights)), weights=weights, k=1)[0]
