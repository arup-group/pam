import random


def freq_sample(freq: float, sample: float, seed: int = None):
    """Down or up sample a frequency based on a sample size. Sub unit frequencies are
    rounded probabalistically.
    :param freq: pre sampled frequency (integer)
    :param sample: sample size (float)
    :params int seed: seed number for reproducible results (None default - does not fix seed).

    :return: new frequency (integer)
    """
    # Fix random seed
    random.seed(seed)

    new_freq = freq * sample
    remainder = new_freq - int(new_freq)
    remainder = int(random.random() < remainder)
    return int(new_freq) + remainder
