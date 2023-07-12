from copy import deepcopy
from typing import Optional

from pam.core import Population
from pam.samplers.basic import freq_sample


def sample(
    population: Population, sample: float, seed: Optional[int] = None, verbose: bool = False
) -> Population:
    """Sample a new population from the existing using a sample size.

    Frequency of returned population is set to 1/sample, eg 0.1 -> 10, such that each household and person represents 10 people from input population.
    Note that in the current implementation frequencies are automatically discovered from the population object households, person and leg weights, in that order.
    When gathering frequencies, for example for a household from multiple person in that houshold, the household frequency is taken as the average person frequency.
    Similarly for persons and their legs.

    Args:
        population (Population): input population object to sample from using population frequency.
        sample (float):  sample size of new population, eg 0.1 for a 10% sample.
        seed (Optional[int], optional): If given, seed number for reproducible results. Defaults to None.
        verbose (bool, optional): Defaults to False.

    Returns:
        Population:
            A new Population object with households sampled based on input frequency.
    """
    sampled_population = Population()
    sample_freq = int(1 / sample)
    size = population.size * sample
    sampled = 0

    for _, hh in population:
        sampled_count = freq_sample(freq=hh.freq, sample=sample, seed=seed)

        for n in range(sampled_count):  # add sampled hhs (note we provide new unique hid)
            sampled_hh = deepcopy(hh)
            sampled_hh.hid = f"{hh.hid}-{n}"
            sampled_hh.people = {}
            sampled_hh.hh_freq = sample_freq

            # add sampled people (note we provide a new unique pid)
            for pid, person in hh.people.items():
                sampled_person = deepcopy(person)
                sampled_person.pid = f"{pid}-{n}"
                sampled_person.person_freq = sample_freq
                sampled_hh.add(sampled_person)

            sampled_population.add(sampled_hh)

        if verbose:
            sampled += sampled_count
            progress = sampled / size
            if progress % 0.01 == 0:
                print(f"Sampled approx. {progress*100}%")

    if verbose:
        print(f"Population sampler completed: {sampled} households from target of {size} sampled")

    return sampled_population
