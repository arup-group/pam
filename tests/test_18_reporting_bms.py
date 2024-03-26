import pandas as pd
from pam.report import benchmarks


def test_get_trips_data(population):
    trips = population.trips_df()
    assert len(trips) == 10
    assert list(trips["mode"]) == [
        "car",
        "car",
        "car",
        "car",
        "bike",
        "bike",
        "bus",
        "bus",
        "pt",
        "pt",
    ]


def test_get_legs_data(population):
    legs = population.legs_df()
    assert len(legs) == 18
    assert list(legs["mode"]) == [
        "car",
        "car",
        "car",
        "car",
        "bike",
        "bike",
        "walk",
        "bus",
        "walk",
        "walk",
        "bus",
        "walk",
        "walk",
        "pt",
        "walk",
        "walk",
        "pt",
        "walk",
    ]


def test_benchmark_trips_hour(population):
    data = population.trips_df()
    bm = benchmarks.create_benchmark(
        data, dimensions=["departure_hour"], data_fields=["freq"], aggfunc=[sum]
    )
    expected_benchmark = pd.DataFrame(
        {"departure_hour": {0: 7, 1: 8, 2: 16, 3: 17}, "freq_sum": {0: 2, 1: 3, 2: 2, 3: 3}}
    )
    assert bm.equals(expected_benchmark)


def test_mode_counts_benchmark(population):
    bm = benchmarks.mode_counts(population)
    expected_benchmark = pd.DataFrame(
        {"mode": {0: "bike", 1: "bus", 2: "car", 3: "pt"}, "trips": {0: 2, 1: 2, 2: 4, 3: 2}}
    )
    assert bm.equals(expected_benchmark)


def test_yield_all_benchmarks(population):
    bms = {path: bm for path, bm in benchmarks.benchmarks(population)}

    for v in bms.values():
        assert sum(v.trips) == 10

    assert list(bms["distances.csv"].trips) == [0, 0, 2, 8, 0, 0, 0, 0]
