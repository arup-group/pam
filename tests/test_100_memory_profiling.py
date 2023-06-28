from pathlib import Path

import pytest
import pandas as pd

from pam import read

BENCHMARK_MEM = "2890.59 MB"
BENCHMARK_SECONDS = 250.64
DATA_DIR = Path(__file__).parent / "test_data"


@pytest.mark.limit_memory(BENCHMARK_MEM)
@pytest.mark.timeout(BENCHMARK_SECONDS)
@pytest.mark.high_mem
def test_activity_loader():
    trips = pd.read_csv(DATA_DIR / "extended_travel_diaries.csv.gz")
    attributes = pd.read_csv(DATA_DIR / "extended_persons_data.csv.gz")
    attributes.set_index("pid", inplace=True)
    read.load_travel_diary(trips, attributes)
