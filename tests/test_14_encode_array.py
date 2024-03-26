from datetime import datetime

import numpy as np
from pam.activity import Activity, Leg, Plan
from pam.array import decode, distance, encode
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY

# One hot


def test_home_plan_to_array():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded, np.stack([np.array((1, 0, 0))] * 24))


def test_home_plan_to_array_alternate():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 1, "work": 2, "travel": 0}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded, np.stack([np.array((0, 1, 0))] * 24))


def test_too_long_plan_to_array():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=END_OF_DAY))
    np.testing.assert_array_equal(
        encode.plan_to_one_hot(
            plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86401
        ),
        np.stack([np.array((1, 0, 0))] * 24),
    )


def test_home_work_plan_to_array_with_hour_bins():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(600), end_time=mtdt(720))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(720), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded[:10, :], np.stack([np.array((1, 0, 0))] * 10))
    np.testing.assert_array_equal(encoded[10:12, :], np.stack([np.array((0, 0, 1))] * 2))
    np.testing.assert_array_equal(encoded[12:, :], np.stack([np.array((0, 1, 0))] * 12))


def test_home_work_plan_to_array_with_half_hour_bins():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(600), end_time=mtdt(720))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(720), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=1800, duration=86400
    )
    np.testing.assert_array_equal(encoded[:20, :], np.stack([np.array((1, 0, 0))] * 20))
    np.testing.assert_array_equal(encoded[20:24, :], np.stack([np.array((0, 0, 1))] * 4))
    np.testing.assert_array_equal(encoded[24:, :], np.stack([np.array((0, 1, 0))] * 24))


def test_rounding_down_to_hour():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(629)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(629), end_time=mtdt(749))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(749), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded[:10, :], np.stack([np.array((1, 0, 0))] * 10))
    np.testing.assert_array_equal(encoded[10:12, :], np.stack([np.array((0, 0, 1))] * 2))
    np.testing.assert_array_equal(encoded[12:, :], np.stack([np.array((0, 1, 0))] * 12))


def test_rounding_up_to_hour():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(599)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(599), end_time=mtdt(719))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(719), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded[:10, :], np.stack([np.array((1, 0, 0))] * 10))
    np.testing.assert_array_equal(encoded[10:12, :], np.stack([np.array((0, 0, 1))] * 2))
    np.testing.assert_array_equal(encoded[12:, :], np.stack([np.array((0, 1, 0))] * 12))


def test_rounding_up_to_hour_2():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(600), end_time=mtdt(629))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(629), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded[:10, :], np.stack([np.array((1, 0, 0))] * 10))
    np.testing.assert_array_equal(encoded[10:, :], np.stack([np.array((0, 1, 0))] * 14))


def test_rounding_out_a_short_component():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(599)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(599), end_time=mtdt(719))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(719), end_time=END_OF_DAY))
    encoded = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    np.testing.assert_array_equal(encoded[:10, :], np.stack([np.array((1, 0, 0))] * 10))
    np.testing.assert_array_equal(encoded[10:12, :], np.stack([np.array((0, 0, 1))] * 2))
    np.testing.assert_array_equal(encoded[12:, :], np.stack([np.array((0, 1, 0))] * 12))


def test_iter_array():
    assert list(
        decode.iter_array(array=np.stack([np.array((1, 0, 0))] * 3), mapping={0: "home"})
    ) == [("home", datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0))]

    assert list(
        decode.iter_array(array=np.stack([np.array((0, 1, 0))] * 3), mapping={0: "home", 1: "work"})
    ) == [("work", datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0))]

    leg = list(
        decode.iter_array(array=np.array([[1, 0, 0], [0, 1, 0]]), mapping={0: "home", 1: "work"})
    )

    assert leg[0] == ("home", datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0))
    assert leg[1] == ("work", datetime(year=1900, month=1, day=1, hour=1, minute=0, second=0))

    leg = list(
        decode.iter_array(
            array=np.array([[1, 0, 0], [1, 0, 0], [0, 1, 0]]), mapping={0: "home", 1: "work"}
        )
    )

    assert leg[0] == ("home", datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0))
    assert leg[1] == ("work", datetime(year=1900, month=1, day=1, hour=2, minute=0, second=0))


def test_add_end_times():
    start_times = [
        datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0) for i in range(3)
    ]
    plan = [Activity(start_time=st) for st in start_times]
    decode.add_end_times(plan)
    for i in range(2):
        assert plan[i].end_time == plan[i + 1].start_time


def test_fix_missing_start_activity():
    start_times = [
        datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0) for i in range(3)
    ]
    plan = [Activity(start_time=st) for st in start_times]
    decode.fix_missing_start_activity(plan)
    assert len(plan) == 3

    start_times = [
        datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0) for i in range(3)
    ]
    plan = [Leg(start_time=st) for st in start_times]
    decode.fix_missing_start_activity(plan)
    assert len(plan) == 4
    assert isinstance(plan[0], Activity)
    assert plan[0].end_time == plan[1].start_time


def test_fix_missing_end_activity():
    start_times = [
        datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0) for i in range(3)
    ]
    plan = [Activity(start_time=st) for st in start_times]
    decode.fix_missing_start_activity(plan)
    assert len(plan) == 3

    start_times = [
        datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0) for i in range(3)
    ]
    plan = [Leg(start_time=st) for st in start_times]
    decode.fix_missing_end_activity(plan)
    assert len(plan) == 4
    assert isinstance(plan[-1], Activity)
    assert plan[-2].end_time == plan[-1].start_time


def test_fix_missing_leg():
    times = [
        (
            datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0),
            datetime(year=1900, month=1, day=1, hour=i + 1, minute=0, second=0),
        )
        for i in range(2)
    ]
    plan = [Activity(start_time=st, end_time=et) for st, et in times]
    decode.fix_missing_components(plan)
    assert len(plan) == 3
    assert isinstance(plan[1], Leg)
    assert plan[0].end_time == datetime(year=1900, month=1, day=1, hour=0, minute=45, second=0)
    assert plan[1].start_time == datetime(year=1900, month=1, day=1, hour=0, minute=45, second=0)
    assert plan[1].end_time == datetime(year=1900, month=1, day=1, hour=1, minute=15, second=0)
    assert plan[2].start_time == datetime(year=1900, month=1, day=1, hour=1, minute=15, second=0)


def test_fix_missing_activity():
    times = [
        (
            datetime(year=1900, month=1, day=1, hour=i, minute=0, second=0),
            datetime(year=1900, month=1, day=1, hour=i + 1, minute=0, second=0),
        )
        for i in range(2)
    ]
    plan = [Leg(start_time=st, end_time=et) for st, et in times]
    decode.fix_missing_components(plan)
    assert len(plan) == 3
    assert isinstance(plan[1], Activity)
    assert plan[0].end_time == datetime(year=1900, month=1, day=1, hour=0, minute=45, second=0)
    assert plan[1].start_time == datetime(year=1900, month=1, day=1, hour=0, minute=45, second=0)
    assert plan[1].end_time == datetime(year=1900, month=1, day=1, hour=1, minute=15, second=0)
    assert plan[2].start_time == datetime(year=1900, month=1, day=1, hour=1, minute=15, second=0)


def test_plan_one_hot_encode_decode_consistent():
    plan = Plan()
    plan.add(Activity(act="home", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(Leg(start_time=mtdt(600), end_time=mtdt(720)))
    plan.add(Activity(act="work", start_time=mtdt(720), end_time=END_OF_DAY))
    encoded_plan = encode.plan_to_one_hot(
        plan=plan, mapping={"home": 0, "work": 1, "travel": 2}, bin_size=3600, duration=86400
    )
    decoded_plan = decode.one_hot_to_plan(
        array=encoded_plan,
        mapping={0: "home", 1: "work", 2: "travel"},
        bin_size=3600,
        duration=86400,
    )
    assert len(decoded_plan) == 3
    for i in range(3):
        assert isinstance(plan[i], type(decoded_plan[i]))
        assert plan[i].act == decoded_plan[i].act
        assert plan[i].start_time == decoded_plan[i].start_time
        assert plan[i].end_time == decoded_plan[i].end_time


def test_accuracy():
    a = np.array([[1, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]])
    b = np.array([[0, 0, 0], [0, 1, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]])
    assert distance.accuracy(a, a) == 1
    assert distance.accuracy(b, b) == 1
    assert distance.accuracy(a, b) == 0.8


def test_one_hot_cross_entropy():
    a = np.array([[1, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]])
    b = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 1, 0], [1, 0, 0]])
    assert 0 < distance.cross_entropy(a, a) < 1e-3
    assert 0 < distance.cross_entropy(b, b) < 1e-3
    assert distance.cross_entropy(a, b) - 22.1048168 < 1e-3


# Categorical


def test_plans_to_cat():
    plan = Plan()
    plan.add(Activity(act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(mode="walk", start_area="A", end_area="B", start_time=mtdt(600), end_time=mtdt(660))
    )
    plan.add(Activity(act="work", area="B", start_time=mtdt(660), end_time=END_OF_DAY))
    encoder = encode.PlansToCategorical(bin_size=3600, duration=86400)
    encoded = encoder.encode(plan)
    np.testing.assert_array_equal(encoded, np.array([0] * 10 + [1] + [2] * 13))
    assert encoder.get_act(0) == "home"
