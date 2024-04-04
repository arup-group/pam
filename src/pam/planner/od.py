"""Manages origin-destination data required by the planner module."""

import itertools
from typing import NamedTuple, Union

import numpy as np


class Labels(NamedTuple):
    """Data labels for the origin-destination dataset."""

    vars: list
    origin_zones: list
    destination_zones: list
    mode: list


class OD:
    """Holds origin-destination matrices for a number of modes and variables."""

    def __init__(self, data: np.ndarray, labels: Union[Labels, list, dict]) -> None:
        """
        Args:
            data (np.ndarray):
                A multi-dimensional numpy array of the origin-destination data.
                - First dimension: variable (ie travel time, distance, etc)
                - Second dimension: origin zone
                - Third dimension: destination zone
                - Fourth dimension: mode (ie car, bus, etc)
            labels (Union[Labels, list, dict]):
        """
        self.data = data
        self.labels = self.parse_labels(labels)
        self.data_checks()

    def data_checks(self):
        """Check the integrity of input data and labels."""
        assert (
            self.data.ndim == 4
        ), "The number of matrix dimensions should be 4 (mode, variable, origin, destination)"
        for i, (key, labels) in enumerate(zip(self.labels._fields, self.labels)):
            assert len(labels) == self.data.shape[i], (
                f"The number of {key} labels should match the number of elements"
                f"in dimension {i} of the OD dataset"
            )

    @staticmethod
    def parse_labels(labels: Union[Labels, list, dict]) -> Labels:
        """Parse labels as a named tuple."""
        if not isinstance(labels, Labels):
            if isinstance(labels, list):
                return Labels(*labels)
            elif isinstance(labels, dict):
                return Labels(**labels)
            else:
                raise ValueError("Please provide a valid label type")
        return labels

    def __getitem__(self, args):
        _args = args if isinstance(args, tuple) else tuple([args])
        _args_encoded = tuple()
        for i, (arg, labels) in enumerate(zip(_args, self.labels)):
            if arg == slice(None) or isinstance(arg, int):
                _args_encoded += (arg,)
            elif arg in labels:
                _args_encoded += (labels.index(arg),)
            else:
                raise IndexError(f"Invalid slice value {arg}")

        return self.data.__getitem__(_args_encoded)

    def __repr__(self) -> str:
        divider = "-" * 50 + "\n"
        r = f"Origin-destination dataset \n{divider}"
        r += f"{self.labels.__str__()}\n{divider}"
        for var in self.labels.vars:
            for trmode in self.labels.mode:
                r += f"{var} - {trmode}:\n"
                r += f"{self[var, :, :, trmode].__str__()}\n{divider}"
        return r


class ODMatrix(NamedTuple):
    var: str
    mode: str
    origin_zones: tuple
    destination_zones: tuple
    matrix: np.array


class ODFactory:
    @classmethod
    def from_matrices(cls, matrices: list[ODMatrix]) -> OD:
        """Creates an OD instance from a list of ODMatrices."""
        # collect dimensions
        labels = cls.prepare_labels(matrices)

        cls.check(matrices, labels)

        # create ndarray
        od = np.zeros(shape=[len(x) for x in labels])
        for mat in matrices:
            od[labels.vars.index(mat.var), :, :, labels.mode.index(mat.mode)] = mat.matrix

        return OD(data=od, labels=labels)

    @staticmethod
    def prepare_labels(matrices: list[ODMatrix]) -> Labels:
        labels = Labels(
            vars=list(dict.fromkeys(mat.var for mat in matrices)),
            origin_zones=matrices[0].origin_zones,
            destination_zones=matrices[0].destination_zones,
            mode=list(dict.fromkeys(mat.mode for mat in matrices)),
        )
        return labels

    @staticmethod
    def check(matrices: list[ODMatrix], labels: Labels) -> None:
        # all matrices follow the same zoning system and are equal size
        for mat in matrices:
            assert mat.origin_zones == labels.origin_zones, "Please check zone labels"
            assert mat.destination_zones == labels.destination_zones, "Please check zone labels"
            assert mat.matrix.shape == matrices[0].matrix.shape, "Please check matrix dimensions"

        # all possible combinations are provided
        combinations_matrices = [(var, trmode) for (var, trmode, *others) in matrices]
        combinations_labels = list(itertools.product(labels.vars, labels.mode))
        for combination in combinations_labels:
            assert (
                combination in combinations_matrices
            ), f"Combination {combination} missing from the input matrices"

        # no duplicate combinations
        assert len(combinations_matrices) == len(
            set(combinations_matrices)
        ), "No duplicate keys are allowed"
