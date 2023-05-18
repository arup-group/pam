import pytest
from pam.planner.od import OD, Labels
import pandas as pd
import numpy as np
from copy import deepcopy


@pytest.fixture
def data_od():
    matrices = np.array(
        [[[[20, 30], [40, 45]], [[40, 45], [20, 30]]],
         [[[5,  5], [8,  9]], [[8,  9], [5,  5]]]]
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


def test_od_slicing_is_correctly_encoded(od):
    np.testing.assert_equal(od[0], od['time'])
    np.testing.assert_equal(od[1], od['distance'])
    np.testing.assert_equal(od[1, 0], od['distance', 'a'])
    np.testing.assert_equal(od[:], od.data)
    np.testing.assert_equal(od[:, :, :, :], od.data)
    np.testing.assert_equal(od['time', 'a', 'b', :], np.array([40, 45]))
    with pytest.raises(IndexError):
        od['_']

def test_class_represantation_is_string(od):
    assert type(od.__repr__()) == str