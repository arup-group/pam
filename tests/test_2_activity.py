from pam.activity import Plan, Activity, Leg, Location
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
import pytest


@pytest.fixture()
def list_of_acts():
    a_1 = Activity(2, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act_2', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_3 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_4 = Activity(2, 'act', 'loc_2', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_5 = Activity(1, '_act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_6 = Activity(2, 'act', 'loc', start_time=mtdt(18 * 60 + 1), end_time=mtdt(19 * 60))
    return [a_1, a_2, a_3, a_4, a_5, a_6]


def test_Activities_are_exact():
    a_1 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert a_1.is_exact(a_2)


def test_Activities_act_differ_and_are_not_exact():
    a_1 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act_2', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_loc_differ_and_are_not_exact():
    a_1 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act', 'loc_2', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_start_time_differ_and_are_not_exact():
    a_1 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act', 'loc', start_time=mtdt(18 * 60 + 1), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_end_time_differ_and_are_not_exact():
    a_1 = Activity(1, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, 'act', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60 +1))

    assert not a_1.is_exact(a_2)


def test_activity_in_list_exact(list_of_acts):
    assert list_of_acts[2].isin_exact(list_of_acts)


def test_very_similar_activity_in_list_exact(list_of_acts):
    v_similar_act = Activity(9999999, 'act_2', 'loc', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    assert v_similar_act.isin_exact(list_of_acts)


def test_activity_with_different_times_not_in_list_exact(list_of_acts):
    different_times_act = Activity(2, 'act_2', 'loc', start_time=mtdt(18 * 60 + 999), end_time=mtdt(19 * 60 + 999))
    assert not different_times_act.isin_exact(list_of_acts)


def test_activity_with_different_times_not_in_list(list_of_acts):
    different_times_act = Activity(2, 'act_2', 'loc', start_time=mtdt(18 * 60 + 999), end_time=mtdt(19 * 60 + 999))
    assert different_times_act in list_of_acts