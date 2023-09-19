import warnings
from typing import Optional

import numpy as np


def safe_divide(x: np.array, y: np.array) -> np.array:
    """Safely divide two arrays. When dividing by zero, the result is set to zero.


    Args:
        x (np.array): Nominator array.
        y (np.array): Denominator array.

    Returns:
        np.array: Divided array.
    """
    return np.divide(x, y, out=np.zeros(x.shape, dtype=np.float64), where=y != 0)


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
        X (np.array): nput matrix
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
