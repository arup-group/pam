from copy import deepcopy

import numpy as np
import pytest
from pam.planner.od import OD, Labels, ODFactory, ODMatrix


@pytest.fixture
def od_matrices():
    zone_labels = ["a", "b"]
    matrices = [
        ODMatrix("time", "car", zone_labels, zone_labels, np.array([[20, 40], [40, 20]])),
        ODMatrix("time", "bus", zone_labels, zone_labels, np.array([[30, 45], [45, 30]])),
        ODMatrix("distance", "car", zone_labels, zone_labels, np.array([[5, 8], [8, 5]])),
        ODMatrix("distance", "bus", zone_labels, zone_labels, np.array([[5, 9], [9, 5]])),
    ]
    return matrices


def test_label_type_is_parsed_correctly(labels):
    assert type(OD.parse_labels(labels)) is Labels
    assert type(OD.parse_labels(list(labels.values()))) is Labels


def test_inconsistent_labels_raise_error(data_od, labels):
    _labels = deepcopy(labels)
    for k, v in _labels.items():
        v.pop()
        with pytest.raises(AssertionError):
            OD(data=data_od, labels=_labels)


def test_od_slicing_is_correctly_encoded(od):
    np.testing.assert_equal(od[0], od["time"])
    np.testing.assert_equal(od[1], od["distance"])
    np.testing.assert_equal(od[1, 0], od["distance", "a"])
    np.testing.assert_equal(od[:], od.data)
    np.testing.assert_equal(od[:, :, :, :], od.data)
    np.testing.assert_equal(od["time", "a", "b", :], np.array([40, 45]))
    with pytest.raises(IndexError):
        od["_"]


def test_class_represantation_is_string(od):
    assert isinstance(od.__repr__(), str)


def test_matrix_dimensions_stay_the_same(od):
    """Regression test: Label dimensions need to stay the same.
    To apply the model correctly,
    we need the first dimension to select the variable,
    the second to select the origin,
    the third to select the destination,
    and the last to select the mode.
    """
    assert od.labels._fields == tuple(["vars", "origin_zones", "destination_zones", "mode"])


def test_create_od_from_matrices(od_matrices, od):
    od_from_matrices = ODFactory.from_matrices(od_matrices)
    np.testing.assert_equal(od_from_matrices.data, od.data)
    assert od_from_matrices.labels == od.labels


def test_od_factory_inconsistent_inputs_raise_error(od_matrices):
    labels = Labels(
        vars=["time", "distance"],
        origin_zones=("a", "b"),
        destination_zones=("a", "b"),
        mode=["car", "bus"],
    )
    # duplicate key
    with pytest.raises(AssertionError):
        ODFactory.check(od_matrices + [od_matrices[0]], labels)

    # combination missing
    with pytest.raises(AssertionError):
        ODFactory.check(od_matrices[:-1], labels)

    # inconsistent zoning
    with pytest.raises(AssertionError):
        ODFactory.check(od_matrices[:-1], labels)
