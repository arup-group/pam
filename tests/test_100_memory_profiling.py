from pathlib import Path

import pandas as pd
import pytest

from pam import read

BENCHMARK_MEM = "2890.59 MB"
BENCHMARK_SECONDS = 285

data_dir = Path(__file__).parent / "test_data"


@pytest.mark.limit_memory(BENCHMARK_MEM)
@pytest.mark.timeout(BENCHMARK_SECONDS)
@pytest.mark.high_mem
def test_activity_loader():
    trips = pd.read_csv(data_dir / "extended_travel_diaries.csv.gz")
    attributes = pd.read_csv(data_dir / "extended_persons_data.csv.gz")
    attributes.set_index("pid", inplace=True)
    read.load_travel_diary(trips, attributes)
