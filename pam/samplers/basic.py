import random
from typing import Optional


def freq_sample(freq: float, sample: float, seed: Optional[int] = None) -> int:
    """Down or up sample a frequency based on a sample size.

    Sub unit frequencies are rounded probabalistically.

    Args:
        freq (float): pre sampled frequency.
        sample (float): sample size.
        seed (Optional[int], optional): If given, seed number for reproducible results. Defaults to None.

    Returns:
        int: new frequency
    """
    # Fix random seed
    random.seed(seed)

    new_freq = freq * sample
    remainder = new_freq - int(new_freq)
    remainder = int(random.random() < remainder)
    return int(new_freq) + remainder
