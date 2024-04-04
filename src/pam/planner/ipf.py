import random
import warnings
from collections import defaultdict
from copy import deepcopy
from typing import Optional

import numpy as np
import pandas as pd

from pam.core import Person, Population
from pam.planner.utils_planner import safe_divide


def get_scaling_factor(X: np.ndarray, sel_dim: int, marginals: np.array) -> np.ndarray:
    """Get the scaling factors required to match a set of marginals for a selected matrix dimension.
        The returned matrix will have the same dimensions as the input matrix

    Args:
        X (np.ndarray): The matrix to be scaled.
        sel_dim (int): The matrix dimension that corresponds to the marginals.
        marginals (np.array): The target values for the selected dimension.

    Returns:
        np.ndarray: A matrix that can be multiplied by the input matrix
            in order to get a new matrix that matches the maginals for the selected dimension.
    """
    other_dims = tuple(i for i in range(X.ndim) if i != sel_dim)
    totals = X.sum(axis=other_dims)
    if ((totals == 0) & (totals != marginals)).sum():
        warnings.warn("Zero-cell issue found! Please check the seed matrix totals.", UserWarning)
    scaling_factor = safe_divide(marginals, totals)
    scaling_factor = np.expand_dims(scaling_factor, other_dims)

    return scaling_factor


def get_max_error(X: np.ndarray, marginals: list[np.array]) -> float:
    """Get the maximum absolute percentage between a matrix and a set of marginals.

    Args:
        X (np.array): Input matrix
        marginals (list[np.array]): a list of marginals

    Returns:
        float: the maximum error value
    """
    max_error = 0
    for dim in range(X.ndim):
        scaling_factor = get_scaling_factor(X, dim, marginals[dim])
        max_error = max(max_error, abs(scaling_factor - 1).max())

    return max_error


def ipf(
    X: np.array,
    marginals: list[np.array],
    tolerance: Optional[float] = 0.001,
    max_iterations: Optional[int] = 10**3,
) -> np.array:
    """Apply Iterative Proportional Fitting on a multi-dimensional matrix.

    Args:
        X (np.array): Initial matrix.
        marginals (list[np.array]): Total to match, one for each matrix dimension.
        tolerance (Optional[float], optional): Max accepted percentage difference to the targets. Defaults to 0.001.
        max_iterations (Optional[int], optional): Max number of iterations. Defaults to 10**3.

    Returns:
        np.array: A fitted matrix that matches the marginals for each dimension.
    """
    X_fitted = X.copy()
    iters = 0
    max_error = get_max_error(X, marginals)
    while (max_error > tolerance) and (iters < max_iterations):
        for sel_dim in range(X_fitted.ndim):
            scaling_factor = get_scaling_factor(X_fitted, sel_dim, marginals[sel_dim])
            X_fitted *= scaling_factor
        iters += 1

    return X_fitted


def prepare_zone_marginals(zone_data: pd.DataFrame) -> tuple[dict, dict[str, list[np.array]]]:
    """Prepare zone marginals in the required format.

    Args:
        zone_data (pd.DataFrame): Zone data, with the zone label as the dataframe index.
            The dataframe columns should follow this convention: `variable|class`,
            for example: `age|minor, age|adult, income|low, income|high, ....`/
            Alternatively, the user can provide a multi-index column format,
            where the first level represents the variable, and the second the class.

    Returns:
        tuple[dict, dict[list[np.array]]]: Zone encodings and marginals.
    """
    df_marginals = zone_data.copy()
    if df_marginals.columns.nlevels != 2:
        df_marginals.columns = pd.MultiIndex.from_tuples(
            [tuple(x.split("|")) for x in df_marginals.columns]
        )

    encodings = defaultdict(list)
    for x, y in df_marginals.columns:
        encodings[x].append(y)

    marginals = {}
    for i, irow in df_marginals.iterrows():
        marginals[i] = irow.groupby(level=0).apply(np.array).loc[list(encodings.keys())].tolist()

    return encodings, marginals


def generate_joint_distributions(
    zone_data: pd.DataFrame,
    tolerance: Optional[float] = 0.001,
    max_iterations: Optional[int] = 10**3,
) -> tuple[dict, dict[str, np.ndarray]]:
    """Generate joint demographic distributions that match zone marginals.

    Args:
        zone_data (pd.DataFrame): Zone data, with the zone label as the dataframe index.
            The dataframe columns should follow this convention: `variable|class`,
            for example: `age|minor, age|adult, income|low, income|high, ....`
        tolerance (Optional[float], optional): Max accepted percentage difference to the targets. Defaults to 0.001.
        max_iterations (Optional[int], optional): Max number of iterations. Defaults to 10**3.

    Returns:
        tuple[dict, dict[np.ndarray]]: Encodings and a matrix of the joint distributions.
    """
    encodings, marginals = prepare_zone_marginals(zone_data)
    dist = {}
    for zone, zone_marginals in marginals.items():
        # start with a small value in each cell
        X = np.zeros(tuple(map(len, zone_marginals))) + 0.001
        # apply iterative proportinal fitting
        fitted = ipf(X, zone_marginals, tolerance=tolerance, max_iterations=max_iterations)
        fitted = fitted.round(0).astype(int)
        dist[zone] = fitted

    return encodings, dist


def get_sample_pool(population: Population, encodings: dict) -> dict[tuple, list[Person]]:
    """Prepares the sample pool for each demographic category.

    Args:
        population (Population): The input PAM population object.
        encodings (dict): Variable encodings generated with `prepare_zone_marginals`.

    Returns:
        dict[tuple, list[Person]]: The sample pool.
            Its index comprises the distribution matrix coordinates (index) for each demographic category.
            Its values consist of the PAM persons belonging in each category.
    """
    person_pool = defaultdict(list)
    for hid, pid, person in population.people():
        code = tuple([v.index(person.attributes[k]) for k, v in encodings.items()])
        person_pool[code].append(person)

    return person_pool


def sample_population(
    encodings: dict, dist: dict[str, np.ndarray], sample_pool: dict[tuple, list[Person]]
) -> Population:
    """Sample a population.

    Args:
        encodings (str): Variable encodings generated with `prepare_zone_marginals`.
        dist (dict[str, np.ndarray]): Joint distribution matrix.
        sample_pool (dict[tuple, list[Person]]): The person sample pool generated wtih `get_sample_pool`.

    Raises:
        ValueError: Zero-cell issue (trying to sample from a category with no seed samples)

    Returns:
        Population: A resampled PAM population.
    """
    pop_fitted = Population()
    n = 0
    for zone, zone_dist in dist.items():
        for code, sample_size in np.ndenumerate(zone_dist):
            if sample_size:
                if code not in sample_pool:
                    # zero cell issue: raise an error
                    k = list(encodings.keys())
                    missing_cat = [([k[i], encodings[k[i]][j]]) for i, j in enumerate(code)]
                    raise ValueError(f"Missing category in seed population: {missing_cat}")
                else:
                    # sample persons from the appropriate demographic group
                    persons = random.choices(sample_pool[code], k=sample_size)
                    # add to the population
                    for person in persons:
                        person_new = deepcopy(person)
                        person_new.pid = f"{person_new.pid}-{n}"
                        person_new.attributes["hzone"] = zone
                        pop_fitted.add(person_new)
                        n += 1

    return pop_fitted


def generate_population(
    population: Population,
    zone_data: pd.DataFrame,
    tolerance: Optional[float] = 0.001,
    max_iterations: Optional[int] = 10**3,
) -> Population:
    """Resample a population and assign its person to zones,
        so that the distributions in the `zone_data` dataset are met.

    Args:
        population (Population): A PAM population.
            Its person attributes should include the controls in the zone data
        zone_data (pd.DataFrame): Zone data, with the zone label as the dataframe index.
            The dataframe columns should follow this convention: `variable|class`,
            for example: `age|minor, age|adult, income|low, income|high, ....`
        tolerance (Optional[float], optional): Max accepted percentage difference to the targets. Defaults to 0.001.
        max_iterations (Optional[int], optional): Max number of iterations. Defaults to 10**3.

    Returns:
        Population: A new population that matches marginals in each zone.
            The household location of each agent is defined under person.attributes['hzone']
    """
    encodings, dist = generate_joint_distributions(
        zone_data, tolerance=tolerance, max_iterations=max_iterations
    )
    sample_pool = get_sample_pool(population, encodings)
    pop_fitted = sample_population(encodings, dist, sample_pool)

    return pop_fitted
