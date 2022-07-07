import os
import pytest

from pam.read import read_matsim
from pam.report import summary


@pytest.fixture
def population():
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plansv12.xml")
    )
    return read_matsim(
        path,
        household_key="hid",
        weight=1,
        version=12
    )


# summary

def test_calc_stats_for_all(population):
    report = summary.calc_stats(
        population=population,
        key = None,
        value = None
    )
    assert report["hhs"] == 2
    assert report["persons"] == 5
    assert report["av_occupancy"] == 2.5


def test_calc_stats_for_slice(population):
    report = summary.calc_stats(
        population=population,
        key = "subpopulation",
        value = "rich"
    )
    assert report["hhs"] == 1
    assert report["persons"] == 2
    assert report["av_occupancy"] == 2


def test_get_attributes(population):
    report = summary.get_attributes(
        population=population,
        key = None,
        value = None
    )
    assert report["subpopulation"] == {"rich", "poor"}
    assert report["hid"] == {"A", "B"}
    assert report["age"] == {"yes", "no"}


def test_get_attributes_by_slice(population):
    report = summary.get_attributes(
        population=population,
        key = "subpopulation",
        value = "rich"
    )
    assert report["hid"] == {"A"}
    assert report["age"] == {"yes", "no"}


def test_count_activites(population):
    report = summary.count_activites(
        population=population,
        key = None,
        value = None
    )
    assert report["home"] == 10


def test_count_activites_by_slice(population):
    report = summary.count_activites(
        population=population,
        key = "subpopulation",
        value = "rich"
    )
    assert report["home"] == 4


def test_count_modes(population):
    report = summary.count_modes(
        population=population,
        key = None,
        value = None
    )
    assert report["car"] == 4
    assert report["bus"] == 2


def test_count_modes_by_slice(population):
    report = summary.count_modes(
        population=population,
        key = "subpopulation",
        value = "rich"
    )
    assert report["car"] == 4
    assert report["bus"] == 0
