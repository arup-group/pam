import numpy as np
from pam.report import stringify, summary

# summary


def test_calc_stats_for_all(population):
    report = summary.calc_stats(population=population, key=None, value=None)
    assert report["hhs"] == 2
    assert report["persons"] == 5
    assert report["av_occupancy"] == 2.5


def test_calc_stats_for_slice(population):
    report = summary.calc_stats(population=population, key="subpopulation", value="rich")
    assert report["hhs"] == 1
    assert report["persons"] == 2
    assert report["av_occupancy"] == 2


def test_get_attributes(population):
    report = summary.get_attributes(population=population, key=None, value=None)
    assert report["subpopulation"] == {"rich", "poor"}
    assert report["hid"] == {"A", "B"}
    assert report["age"] == {"yes", "no"}


def test_get_attributes_by_slice(population):
    report = summary.get_attributes(population=population, key="subpopulation", value="rich")
    assert report["hid"] == {"A"}
    assert report["age"] == {"yes", "no"}


def test_count_activites(population):
    report = summary.count_activites(population=population, key=None, value=None)
    assert report["home"] == 10


def test_count_activites_by_slice(population):
    report = summary.count_activites(population=population, key="subpopulation", value="rich")
    assert report["home"] == 4


def test_count_modes(population):
    report = summary.count_modes(population=population, key=None, value=None)
    assert report["car"] == 4
    assert report["bus"] == 2


def test_count_modes_by_slice(population):
    report = summary.count_modes(population=population, key="subpopulation", value="rich")
    assert report["car"] == 4
    assert report["bus"] == 0


def test_inf_yield():
    infy = stringify.inf_yield([0, 1, 2])
    y = [next(infy) for i in range(6)]
    assert y == [0, 1, 2, 0, 1, 2]


def test_stringify_colourer():
    colour = stringify.ActColour()
    assert colour.paint("travel", "travel") == "\033[38;5;232mtravel\033[0m"
    assert colour.paint("A", "A") == "\033[38;5;21mA\033[0m"


def test_stringify_colourer_bw():
    colour = stringify.ActColour(colour=False)
    assert colour.paint("travel", "travel") == "\033[38;5;232mtravel\033[0m"
    assert colour.paint("B", "B") == "\033[38;5;255mB\033[0m"


def test_stringify_plan():
    assert (
        stringify.stringify_plan(
            plan_array=np.array((0, 1)),
            mapping={0: "travel", 1: "act"},
            colourer=stringify.ActColour(colour=True),
        )
        == "\033[38;5;232m▇\033[0m\033[38;5;21m▇\033[0m"
    )
