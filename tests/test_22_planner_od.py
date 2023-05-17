import pytest
from pam.planner.od import OD, Labels
import pandas as pd
import numpy as np
from copy import deepcopy


@pytest.fixture
def data_od():
    matrices = np.array(
        [
            [
                [[20, 40], [40, 20]],
                [[5, 8], [8, 5]]
            ],
            [
                [[30, 45], [45, 30]],
                [[5, 8], [8, 5]]
            ]
        ]
    )
    return matrices


@pytest.fixture
def labels():
    labels = {
        'mode': ['car', 'bus'],
        'vars': ['time', 'distance'],
        'origin_zones': ['a', 'b'],
        'destination_zones': ['a', 'b']
    }
    return labels


@pytest.fixture
def od(data_od, labels):
    od = OD(
        data=data_od,
        labels=labels
    )
    return od


def test_label_type_is_parsed_correctly(labels):
    assert type(OD.parse_labels(labels)) is Labels
    assert type(OD.parse_labels(list(labels.values()))) is Labels


def test_inconsistent_labels_raise_error(data_od, labels):
    _labels = deepcopy(labels)
    for k, v in _labels.items():
        v.pop()
        with pytest.raises(AssertionError):
            OD(
                data=data_od,
                labels=_labels
            )
