from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from pam.core import Household, Population
from pam.plot.plans import (
    build_cmap,
    build_person_df,
    build_person_travel_geodataframe,
    build_rgb_travel_cmap,
    plot_activities,
    plot_activity_breakdown_area,
    plot_activity_breakdown_area_tiles,
)
from pam.plot.stats import (
    calculate_leg_duration_by_mode,
    extract_activity_log,
    extract_leg_log,
    plot_activity_times,
    plot_leg_times,
    plot_population_comparisons,
    time_binner,
)
from pam.policy import policies
from pam.variables import DEFAULT_ACTIVITIES_FONTSIZE, DEFAULT_ACTIVITIES_PLOT_WIDTH
from plotly.graph_objs import Scattermapbox
from shapely.geometry import Point


@pytest.fixture
def person_df(person_heh):
    return build_person_df(person_heh)


def test_build_person_dataframe(person_df):
    assert len(person_df) == 5
    assert list(person_df.act) == ["Home", "Travel", "Education", "Travel", "Home"]


def test_build_cmap_dict():
    df = pd.DataFrame(
        [
            {"act": "Home", "dur": None},
            {"act": "Travel", "dur": None},
            {"act": "Work", "dur": None},
            {"act": "Travel", "dur": None},
            {"act": "Home", "dur": None},
        ]
    )
    cmap = build_cmap(df)
    assert isinstance(cmap, dict)
    assert set(list(cmap)) == set(["Home", "Work", "Travel"])


def test_build_rgb_travel_cmap(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = build_person_travel_geodataframe(Steve)
    cmap = build_rgb_travel_cmap(gdf, colour_by="mode")
    assert cmap == {"car": (255, 237, 111), "walk": (204, 235, 197)}


def test_build_activity_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    assert len(log) == 15
    assert list(log.columns) == ["act", "start", "end", "duration"]


def test_build_leg_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_leg_log(population)
    assert len(log) == 10
    assert list(log.columns) == ["mode", "start", "end", "duration"]


def test_time_binner(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    binned = time_binner(log)
    assert len(binned) == 96
    for h in ["start", "end", "duration"]:
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
    population_1.name = "base"
    population_2 = deepcopy(population_1)
    population_2.name = "work_removed"

    policy_remove_work = policies.RemovePersonActivities(activities=["work"], probability=1)
    policies.apply_policies(population_2, [policy_remove_work])

    list_of_populations = [population_1, population_2]
    outputs = plot_population_comparisons(list_of_populations, "home")
    legs = outputs[2]
    outputs[3]
    check = calculate_leg_duration_by_mode(population_2)
    assert isinstance(outputs[0], Figure)
    assert isinstance(outputs[1], Figure)
    assert (
        legs.loc["work_removed", "walk"]
        == check.loc[check["leg mode"] == "walk", "duration_hours"].iloc[0]
    )


def test_plot_travel_plans(cyclist):
    fig = cyclist.plot_travel_plotly(mapbox_access_token="token")
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], Scattermapbox)
    assert fig.data[0].name == "bike"


def test_plot_travel_plans_coloured_by_purp(pt_person):
    fig = pt_person.plot_travel_plotly(colour_by="pid", mapbox_access_token="token")
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], Scattermapbox)
    assert fig.data[0].name == "census_1"


def test_plot_travel_plans_grouped_by_legs(pt_person):
    fig = pt_person.plot_travel_plotly(groupby=["seq"], mapbox_access_token="token")
    for dat in fig.data:
        assert isinstance(dat, Scattermapbox)
    assert [dat.name for dat in fig.data] == [
        "('pt', 3)",
        "('pt', 5)",
        "('pt', 7)",
        "('transit_walk', 1)",
        "('transit_walk', 2)",
        "('transit_walk', 4)",
        "('transit_walk', 6)",
        "('transit_walk', 8)",
    ]


def test_plot_travel_plans_for_household(instantiate_household_with, cyclist, pt_person):
    hhld = instantiate_household_with([cyclist, pt_person])
    fig = hhld.plot_travel_plotly(mapbox_access_token="token")
    assert len(fig.data) == 3
    assert [dat.name for dat in fig.data] == ["bike", "pt", "transit_walk"]


def test_plot_activities(person_df):
    fig, ax = plot_activities(person_df)
    assert isinstance(ax, Axes)
    assert isinstance(fig, Figure)
    assert any(isinstance(i, Legend) for i in fig.get_children())


def test_plot_activities_no_legend(person_df):
    fig, ax = plot_activities(person_df, legend=False)
    assert not any(isinstance(i, Legend) for i in fig.get_children())


def test_plot_activities_user_defined_cmap(person_df):
    cmap = {"Home": (1, 1, 1), "Education": (0, 0, 0), "Travel": (0.3, 0.3, 0.3)}
    default_opacity = 1
    fig, ax = plot_activities(person_df, cmap=cmap)
    for idx, patch in enumerate(ax.patches):
        label = ax.texts[idx].get_text()
        fc = patch.get_facecolor()
        # assertion is against rgba values (i.e., including an opacity value)
        assert cmap[label] + (default_opacity,) == fc


def test_plot_activities_expected_auto_fontcolor(person_df):
    "Label fontcolour is selected based on perceived luminance of background colour"
    cmap = {"Home": (1, 1, 1), "Education": (0, 0, 0), "Travel": (0.3, 0.3, 0.3)}
    expected_fontcolor = {"Home": "black", "Education": "white", "Travel": "white"}
    fig, ax = plot_activities(person_df, cmap=cmap)
    for text in ax.texts:
        assert text.get_color() == expected_fontcolor[text.get_text()]


def test_plot_activities_non_default_label_fontsize_partial(person_df):
    "All undefined fontsizes should default to the system default (scaled if fig width has changed from the default)"
    fontsizes = {"Home": 20}
    fig, ax = plot_activities(person_df, label_fontsize={"Home": 20})
    for text in ax.texts:
        assert text.get_fontsize() == fontsizes.get(text.get_text(), DEFAULT_ACTIVITIES_FONTSIZE)


def test_plot_activities_non_default_label_fontsize_all(person_df):
    fontsizes = {"Home": 20, "Education": 5, "Travel": 15}
    fig, ax = plot_activities(person_df, label_fontsize=fontsizes)
    for text in ax.texts:
        assert text.get_fontsize() == fontsizes[text.get_text()]


def test_plot_activities_non_default_fig_width(person_df):
    width = 40
    scaled_fontsize = DEFAULT_ACTIVITIES_FONTSIZE * width / DEFAULT_ACTIVITIES_PLOT_WIDTH
    fig, ax = plot_activities(person_df, width=width)

    assert fig.get_figwidth() == width
    assert ax.title.get_fontsize() == scaled_fontsize


def test_plot_activity_breakdown_returns_axis(population_heh):
    ax = plot_activity_breakdown_area(list(population_heh.plans()), population_heh.activity_classes)
    assert isinstance(ax, Axes)


def test_plot_activity_breakdown_tiles_shape(population_heh):
    plans = {i: list(population_heh.plans()) for i in range(4)}
    axs = plot_activity_breakdown_area_tiles(plans, population_heh.activity_classes)
    assert isinstance(axs, np.ndarray)
    assert axs.shape == (2, 2)
