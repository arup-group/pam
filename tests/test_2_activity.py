from pam.activity import Plan, Activity, Leg, Location
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


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