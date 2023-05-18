"""
Manages origin-destination data required by the planner module.
"""
import numpy as np
from typing import Union, Optional, List, NamedTuple


class Labels(NamedTuple):
    """ Data labels for the origin-destination dataset """
    vars: List
    origin_zones: List
    destination_zones: List
    mode: List


class OD:
    """
    Holds origin-destination matrices for a number of modes and variables.
    """
    dimensions = ['mode', 'variable', 'origin', 'destination']

    def __init__(
        self,
        data: np.ndarray,
        labels: Union[Labels, List, dict]
    ) -> None:
        """
        :param data: A multi-dimensional numpy array of the origin-destination data.
            - First dimension: mode (ie car, bus, etc)
            - Second dimension: variable (ie travel time, distance, etc)
            - Third dimension: origin zone
            - Fourth dimension: destination zone
        """
        self.data = data
        self.labels = self.parse_labels(labels)
        self.data_checks()

    def data_checks(self):
        """
        Check the integrity of input data and labels.
        """
        assert self.data.ndim == 4, \
            "The number of matrix dimensions should be 4 (mode, variable, origin, destination)"
        for i, (key, labels) in enumerate(zip(self.labels._fields, self.labels)):
            assert len(labels) == self.data.shape[i], \
                f"The number of {key} labels should match the number of elements" \
                f"in dimension {i} of the OD dataset"

    @staticmethod
    def parse_labels(labels: Union[Labels, List, dict]) -> Labels:
        """
        Parse labels as a named tuple.
        """
        if not isinstance(labels, Labels):
            if isinstance(labels, list):
                return Labels(*labels)
            elif isinstance(labels, dict):
                return Labels(**labels)
            else:
                raise ValueError('Please provide a valid label type')
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
                raise IndexError(f'Invalid slice value {arg}')

        return self.data.__getitem__(_args_encoded)

    def __repr__(self) -> str:
        divider = '-'*50 + '\n'
        r = f'Origin-destination dataset \n{divider}'
        r += f'{self.labels.__str__()}\n{divider}'
        for var in self.labels.vars:
            for trmode in self.labels.mode:
                r += f'{var} - {trmode}:\n'
                r += f'{self[var, :, :, trmode].__str__()}\n{divider}'
        return r
