from pathlib import Path

import pandas as pd
import pytest
from pam import read

BENCHMARK_MEM = "1400 MB"
BENCHMARK_SECONDS = 250

data_dir = Path(__file__).parent / "test_data"


@pytest.fixture(scope="module")
def trips_attrs():
    trips = pd.read_csv(data_dir / "extended_travel_diaries.csv.gz")
    attributes = pd.read_csv(data_dir / "extended_persons_data.csv.gz")
    attributes.set_index("pid", inplace=True)
    return trips, attributes


@pytest.mark.limit_memory(BENCHMARK_MEM)
@pytest.mark.high_mem
def test_activity_loader_mem(trips_attrs):
    read.load_travel_diary(*trips_attrs)


@pytest.mark.timeout(BENCHMARK_SECONDS, func_only=True)
@pytest.mark.high_mem
def test_activity_loader_time(trips_attrs):
    read.load_travel_diary(*trips_attrs)
