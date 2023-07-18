import pytest
from shapely import Point

from pam.activity import Activity, Leg, Plan


@pytest.mark.parametrize(
    ["day", "expected"],
    [
        ([], []),
        ([Activity(act="home", loc=Point(0, 0))], []),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="work", loc=Point(100, 0)),
            ],
            [Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0))],
        ),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="pt interaction", loc=Point(100, 0)),
                Leg(mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)),
                Activity(act="pt interaction", loc=Point(100, 1000)),
                Leg(mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
            ],
            [Leg(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000))],
        ),
    ],
)
def test_iter_trips(day, expected):
    plan = Plan()
    plan.day = day
    assert list(plan.trips()) == expected


@pytest.mark.parametrize(
    ["day", "expected"],
    [
        ([], []),
        ([Activity(act="home", loc=Point(0, 0))], [Activity(act="home", loc=Point(0, 0))]),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="work", loc=Point(100, 0)),
            ],
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="work", loc=Point(100, 0)),
            ],
        ),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="pt interaction", loc=Point(100, 0)),
                Leg(mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)),
                Activity(act="pt interaction", loc=Point(100, 1000)),
                Leg(mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
            ],
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
            ],
        ),
    ],
)
def test_tripify(day, expected):
    plan = Plan()
    plan.day = day
    assert list(plan.tripify()) == expected
