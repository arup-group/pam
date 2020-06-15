import random


def freq_sample(freq: int, sample: float):
    """
    Down or up sample a frequency based on a sample size. Sub unit frequencies are
    rounded probabalistically.
    :param freq: pre sampled frequency (integer)
    :param sample: sample size (float)
    :return: new frequency (integer)
    """
    new_freq = freq * sample
    remainder = new_freq - int(new_freq)
    remainder = int(random.random() < remainder)
    return int(new_freq) + remainder
