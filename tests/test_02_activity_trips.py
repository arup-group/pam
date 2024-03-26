import pytest
from pam.activity import Activity, Leg, Plan, Trip
from shapely import Point


@pytest.mark.parametrize(
    "day,expected",
    [
        ([], []),
        ([Activity(act="home", loc=Point(0, 0))], []),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="work", loc=Point(100, 0)),
            ],
            [Trip(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0))],
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
            [Trip(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000))],
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
                Leg(mode="car", distance=1200, start_loc=Point(100, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
            [
                Trip(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000)),
                Trip(mode="car", distance=1200, start_loc=Point(0, 1000), end_loc=Point(0, 0)),
            ],
        ),
    ],
)
def test_iter_trips(day, expected):
    plan = Plan()
    plan.day = day
    assert list(plan.trips()) == expected


@pytest.mark.parametrize(
    "day,expected",
    [
        ([], []),
        ([Activity(act="home", loc=Point(0, 0))], []),
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="work", loc=Point(100, 0)),
            ],
            [[Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0))]],
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
                [
                    Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                    Leg(
                        mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)
                    ),
                    Leg(
                        mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)
                    ),
                ]
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
                Leg(mode="car", distance=1200, start_loc=Point(100, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
            [
                [
                    Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                    Leg(
                        mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)
                    ),
                    Leg(
                        mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)
                    ),
                ],
                [Leg(mode="car", distance=1200, start_loc=Point(100, 1000), end_loc=Point(0, 0))],
            ],
        ),
    ],
)
def test_iter_trip_legs(day, expected):
    plan = Plan()
    plan.day = day
    assert list(plan.trip_legs()) == expected


@pytest.mark.parametrize(
    "day",
    [
        [],
        [Activity(act="home", loc=Point(0, 0))],
        [
            Activity(act="home", loc=Point(0, 0)),
            Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
            Activity(act="work", loc=Point(100, 0)),
        ],
    ],
)
def test_tripify_unchanged(day):
    plan = Plan()
    plan.day = day.copy()
    assert list(plan.tripify()) == day


@pytest.mark.parametrize(
    "day,expected",
    [
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
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="pt interaction", loc=Point(100, 0)),
                Leg(mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)),
                Activity(act="pt interaction", loc=Point(100, 1000)),
                Leg(mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
                Leg(mode="car", distance=1200, start_loc=Point(0, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
                Leg(mode="car", distance=1200, start_loc=Point(0, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
        ),
    ],
)
def test_tripify_changed(day, expected):
    plan = Plan()
    plan.day = day
    assert list(plan.tripify()) == expected


@pytest.mark.parametrize(
    "day",
    [
        [],
        [Activity(act="home", loc=Point(0, 0))],
        [
            Activity(act="home", loc=Point(0, 0)),
            Leg(mode="car", distance=1000, start_loc=Point(0, 0), end_loc=Point(100, 0)),
            Activity(act="work", loc=Point(100, 0)),
        ],
    ],
)
def test_simplify_pt_trips_unchanged(day):
    plan = Plan()
    plan.day = day.copy()
    plan.simplify_pt_trips()
    assert plan.day == day


@pytest.mark.parametrize(
    "day,expected",
    [
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
        (
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="walk", distance=100, start_loc=Point(0, 0), end_loc=Point(100, 0)),
                Activity(act="pt interaction", loc=Point(100, 0)),
                Leg(mode="bus", distance=1000, start_loc=Point(100, 0), end_loc=Point(100, 1000)),
                Activity(act="pt interaction", loc=Point(100, 1000)),
                Leg(mode="walk", distance=20, start_loc=Point(100, 1000), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
                Leg(mode="car", distance=1200, start_loc=Point(0, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
            [
                Activity(act="home", loc=Point(0, 0)),
                Leg(mode="bus", distance=1120, start_loc=Point(0, 0), end_loc=Point(0, 1000)),
                Activity(act="work", loc=Point(0, 1000)),
                Leg(mode="car", distance=1200, start_loc=Point(0, 1000), end_loc=Point(0, 0)),
                Activity(act="home", loc=Point(0, 0)),
            ],
        ),
    ],
)
def test_simplify_pt_trips_changed(day, expected):
    plan = Plan()
    plan.day = day
    plan.simplify_pt_trips()
    assert plan.day == expected
