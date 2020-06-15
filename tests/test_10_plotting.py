import pytest
import pandas as pd
from matplotlib.figure import Figure

from pam.plot.plans import build_person_df, build_cmap
from pam.plot.stats import extract_activity_log, extract_leg_log, time_binner, plot_activity_times, plot_leg_times, plot_population_comparisons, calculate_leg_duration_by_mode
from .fixtures import person_heh, Steve, Hilda
from pam.core import Household, Population
from copy import deepcopy
from pam import modify


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


def test_plot_act_time_bins(Steve, Hilda):
    population = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population.add(hh)
    fig = plot_activity_times(population)
    assert isinstance(fig, Figure)


def test_plot_leg_time_bins(Steve, Hilda):
    population = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population.add(hh)
    fig = plot_leg_times(population)
    assert isinstance(fig, Figure)

def test_plot_population_comparisons(Steve, Hilda):
    population_1 = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population_1.add(hh)
    population_1.name = 'base'
    population_2 = deepcopy(population_1)
    population_2.name = 'work_removed'
    
    policy_remove_work = modify.ActivityPolicy(
    policy=modify.RemoveActivity(['work']),
    probability=1)
    modify.apply_policies(population_2, [policy_remove_work])
    
    list_of_populations = [population_1, population_2]
    outputs = plot_population_comparisons(list_of_populations, 'home')
    legs = outputs[2]
    activities = outputs[3]
    check = calculate_leg_duration_by_mode(population_2)
    assert isinstance(outputs[0], Figure)
    assert isinstance(outputs[1], Figure)
    assert legs.loc['work_removed', 'walk'] == check.loc[check['leg mode'] == 'walk', 'duration_hours'].iloc[0]
   