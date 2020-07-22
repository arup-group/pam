import pytest
import pandas as pd
from matplotlib.figure import Figure
from shapely.geometry import Point, LineString
from pandas.testing import assert_frame_equal
from plotly.graph_objs import Scattermapbox


from pam.plot.plans import build_person_df, build_cmap, build_person_travel_geodataframe, build_rgb_travel_cmap, \
    plot_travel_plans
from pam.plot.stats import extract_activity_log, extract_leg_log, time_binner, plot_activity_times, plot_leg_times, \
    plot_population_comparisons, calculate_leg_duration_by_mode
from .fixtures import person_heh, Steve, Hilda, instantiate_household_with
from pam.core import Household, Population
from copy import deepcopy
from pam.policy import policies


def test_build_person_dataframe(person_heh):
    df = build_person_df(person_heh)
    assert len(df) == 5
    assert list(df.act) == ['Home', 'Travel', 'Education', 'Travel', 'Home']


def test_build_cmap_dict():
    df = pd.DataFrame(
        [
            {'act': 'Home', 'dur': None},
            {'act': 'Travel', 'dur': None},
            {'act': 'Work', 'dur': None},
            {'act': 'Travel', 'dur': None},
            {'act': 'Home', 'dur': None},
        ]
    )
    cmap = build_cmap(df)
    assert isinstance(cmap, dict)
    assert set(list(cmap)) == set(['Home', 'Work', 'Travel'])


def test_build_rgb_travel_cmap(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = build_person_travel_geodataframe(Steve)
    cmap = build_rgb_travel_cmap(gdf, colour_by='mode')
    assert cmap == {'car': (255, 237, 111), 'walk': (204, 235, 197)}


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

    policy_remove_work = policies.RemovePersonActivities(
        activities=['work'],
        probability=1
    )
    policies.apply_policies(population_2, [policy_remove_work])

    list_of_populations = [population_1, population_2]
    outputs = plot_population_comparisons(list_of_populations, 'home')
    legs = outputs[2]
    activities = outputs[3]
    check = calculate_leg_duration_by_mode(population_2)
    assert isinstance(outputs[0], Figure)
    assert isinstance(outputs[1], Figure)
    assert legs.loc['work_removed', 'walk'] == check.loc[check['leg mode'] == 'walk', 'duration_hours'].iloc[0]


def test_plot_travel_plans(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = build_person_travel_geodataframe(Steve)
    fig = plot_travel_plans(gdf, mapbox_access_token='token')
    assert len(fig.data) == 2
    assert isinstance(fig.data[0], Scattermapbox)
    assert isinstance(fig.data[1], Scattermapbox)
    assert fig.data[0].name == 'car'
    assert fig.data[1].name == 'walk'


def test_plot_travel_plans_coloured_by_purp(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
        leg.purp = 'purp'
    gdf = build_person_travel_geodataframe(Steve)
    fig = plot_travel_plans(gdf, colour_by='purp', mapbox_access_token='token')
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], Scattermapbox)
    assert fig.data[0].name == 'purp'


def test_plot_travel_plans_grouped_by_legs(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = build_person_travel_geodataframe(Steve)
    fig = plot_travel_plans(gdf, groupby=['seq'], mapbox_access_token='token')
    for i in range(4):
        assert isinstance(fig.data[i], Scattermapbox)
    assert [fig.data[i].name for i in range(4)] == ["('car', 1)", "('car', 4)", "('walk', 2)", "('walk', 3)"]


def test_plot_travel_plans_for_household(Steve, Hilda):
    hhld = instantiate_household_with([Steve, Hilda])
    for pid, person in hhld:
        for leg in person.legs:
            leg.start_location.loc = Point(1, 2)
            leg.end_location.loc = Point(2, 3)
    gdf = hhld.build_travel_geodataframe()
    fig = plot_travel_plans(gdf, groupby=['seq'], mapbox_access_token='token')


def test_plot_travel_plans_for_household_method(Steve, Hilda):
    hhld = instantiate_household_with([Steve, Hilda])
    for pid, person in hhld:
        for leg in person.legs:
            leg.start_location.loc = Point(1, 2)
            leg.end_location.loc = Point(2, 3)
    fig = hhld.plot_travel_plotly(mapbox_access_token='token')
