import os
import pytest
import pandas as pd
from datetime import datetime

from pam.core import Population, Activity, minutes_to_datetime


testdata = [
    (0, datetime(2020, 4, 2, 0, 0)),
    (30, datetime(2020, 4, 2, 0, 30)),
    (300, datetime(2020, 4, 2, 5, 0)),
    (330, datetime(2020, 4, 2, 5, 30)),
]


@pytest.mark.parametrize("m,expected", testdata)
def test_minutes_to_dt(m, expected):
    assert minutes_to_datetime(m) == expected
