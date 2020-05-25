import pytest
import pandas as pd

from pam.plot.plans import build_person_df, build_cmap
from pam.plot.stats import extract_activity_log, extract_leg_log, time_binner
from .fixtures import person_heh
from pam.core import Household, Population


def test_build_person_dataframe(person_heh):
    df = build_person_df(person_heh)
    assert len(df) == 5
    assert list(df.act) == ['Home', 'Travel', 'Education', 'Travel', 'Home']


def test_build_cmap_dict():
    df = pd.DataFrame(
        [
            {'act':'Home', 'dur':None},
            {'act':'Travel', 'dur':None},
            {'act':'Work', 'dur':None},
            {'act':'Travel', 'dur':None},
            {'act':'Home', 'dur':None},
        ]
    )
    cmap = build_cmap(df)
    assert isinstance(cmap, dict)
    assert set(list(cmap)) == set(['Home', 'Work', 'Travel'])


def test_build_activity_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    assert len(log) == 15
    assert list(log.columns) == ['act', 'start', 'end', 'duration']


def test_build_leg_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_leg_log(population)
    assert len(log) == 10
    assert list(log.columns) == ['mode', 'start', 'end', 'duration']


def test_time_binner(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    binned = time_binner(log)
    assert len(binned) == 96
    for h in ['start', 'end', 'duration']:
        assert binned[h].sum() == 3
