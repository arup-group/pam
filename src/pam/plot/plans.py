from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pam.activity import Plan
    from pam.core import Person

import warnings

import matplotlib
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
from shapely.errors import ShapelyDeprecationWarning

import pam.activity as activity
import pam.utils as utils
from pam.planner import encoder
from pam.variables import DEFAULT_ACTIVITIES_FONTSIZE, DEFAULT_ACTIVITIES_PLOT_WIDTH


def plot_person(person, **kwargs):
    df = build_person_df(person)
    plot_activities(df, **kwargs)


def plot_persons(persons, **kwargs):
    df = pd.concat([build_person_df(person) for person in persons])
    plot_activities(df, **kwargs)


def plot_household(household, **kwargs):
    df = pd.concat([build_person_df(person) for person in household.people.values()])
    plot_activities(df, **kwargs)


def build_plan_df(plan, pid="sample"):
    """Loop through a plan, creating a pandas dataframe defining activities for plotting."""
    data = {"act": [], "modes": [], "start_time": [], "end_time": [], "dur": []}
    for component in plan.day:
        data["act"].append(component.act.lower().title())
        if isinstance(component, activity.Leg) and component.mode is not None:
            data["modes"].append(component.mode.lower().title())
        else:
            data["modes"].append(None)
        data["start_time"].append(component.start_time.hour + component.start_time.minute / 60)
        data["end_time"].append(component.end_time.hour + component.end_time.minute / 60)
        data["dur"].append(component.duration.total_seconds() / 3600)
    df = pd.DataFrame(data)
    df["pid"] = pid

    return df


def plot_plan(plan, **kwargs):
    df = build_plan_df(plan)
    plot_activities(df, **kwargs)


def build_person_df(person):
    """Loop through a persons plan, creating a pandas dataframe defining activities for plotting."""
    data = {"act": [], "modes": [], "start_time": [], "end_time": [], "dur": []}
    for component in person.plan.day:
        data["act"].append(component.act.lower().title())
        if isinstance(component, activity.Leg):
            data["modes"].append(component.mode.lower().title())
        else:
            data["modes"].append(None)
        data["start_time"].append(component.start_time.hour + component.start_time.minute / 60)
        data["end_time"].append(component.end_time.hour + component.end_time.minute / 60)
        data["dur"].append(component.duration.total_seconds() / 3600)
    df = pd.DataFrame(data)
    df["pid"] = person.pid

    return df


def build_person_travel_geodataframe(
    person: Person, from_epsg: Optional[str] = None, to_epsg: Optional[str] = None
) -> GeoDataFrame:
    """Loop through a persons legs, creating a geopandas GeoDataFrame defining travel for plotting.

    Args:
      person (pam.core.Person):
      from_epsg (str, optional):
        coordinate system the plans are currently in.
        You need to specify `from_epsg` as well to use this. Defaults to None.
      to_epsg (str, optional):
        coordinate system you want the geo dataframe to be projected to.
        You need to specify `from_epsg` as well to use this. Defaults to None.

    Returns:
        GeoDataFrame: geographically pinpointed travel legs for given `person`.

    """
    df = pd.DataFrame()
    for leg in person.legs:
        if (leg.start_location.loc is None) or (leg.end_location.loc is None):
            raise AttributeError(
                """
To create a geopandas.DataFrame you need specific locations. Make sure Legs have
loc attribute defined with a shapely.Point or s2sphere.CellId.
"""
            )
        geometry = utils.get_linestring(leg.start_location.loc, leg.end_location.loc)
        _leg_dict = {
            "mode": leg.mode,
            "purp": leg.purp,
            "seq": leg.seq,
            "freq": leg.freq,
            "start_time": leg.start_time,
            "end_time": leg.end_time,
            "start_location": geometry.coords[0],
            "end_location": geometry.coords[-1],
            "geometry": geometry,
            "distance": leg.distance,
            "service_id": leg.route.transit.get("transitLineId"),
            "route_id": leg.route.transit.get("transitRouteId"),
            "o_stop": leg.route.transit.get("accessFacilityId"),
            "d_stop": leg.route.transit.get("egressFacilityId"),
            "network_route": leg.route.network_route,
        }

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
            df = pd.concat([df, pd.Series(_leg_dict)], ignore_index=True, axis=1)

    df = df.T.infer_objects()
    df["pid"] = person.pid
    df = GeoDataFrame(df, geometry="geometry")
    if from_epsg:
        df.crs = from_epsg
        if to_epsg:
            df = df.to_crs(to_epsg)

    return df


def build_rgb_travel_cmap(df, colour_by):
    colors = [
        (int(tup[0] * 255), int(tup[1] * 255), int(tup[2] * 255))
        for tup in plt.cm.Set3.colors[::-1]
    ]
    colour_by_unique = df[colour_by].unique()
    # repeat colours if unique items > 12
    len_factor = (len(colour_by_unique) // len(colors)) + 1
    d_color = dict(zip(colour_by_unique, colors * len_factor))
    return d_color


def build_cmap(df: pd.DataFrame) -> dict:
    colors = plt.cm.Set3.colors[::-1]
    activities_unique = df["act"].unique()
    # repeat colours if unique items > 1
    len_factor = (len(activities_unique) // len(colors)) + 1
    d_color = dict(zip(activities_unique, colors * len_factor))
    d_color["Travel"] = (0.3, 0.3, 0.3)
    return d_color


def plot_activities(
    df: pd.DataFrame,
    cmap: Optional[dict] = None,
    width: int = DEFAULT_ACTIVITIES_PLOT_WIDTH,
    legend: bool = True,
    label_fontsize: Optional[Union[dict, int]] = None,
    path: Optional[Union[str, Path]] = None,
) -> None:
    """Plot activity plans from pandas dataframe.

    Args:
        df (pd.DataFrame): Input activity plan data
        cmap (Optional[dict], optional): Map from activity to colour. If not given, random colours will be applied from `Set3`. Defaults to None.
        width (int, optional): Figure width. Defaults to DEFAULT_ACTIVITIES_PLOT_WIDTH.
        legend (bool, optional): If True, a legend will be added to the bottom of the figure. Defaults to True.
        label_fontsize (Union[dict, int], optional): Set fontsize of activity / trip labels using a mapping or a single value to apply to all labels. This can be a partial mapping, with those _not_ defined defaulting to a fontsize of DEFAULT_ACTIVITIES_FONTSIZE. Defaults to None.
        path (Optional[str  |  Path], optional): If given, path to which the figure should be saved. Defaults to None.
    """
    if cmap is None:
        cmap = build_cmap(df)
    fontscale = width / DEFAULT_ACTIVITIES_PLOT_WIDTH
    scaled_fontsize = DEFAULT_ACTIVITIES_FONTSIZE * fontscale

    df["color"] = df["act"].map(cmap)
    pids = df["pid"].unique()

    fig, axs = plt.subplots(
        len(pids),
        1,
        figsize=(width, 0.5 + 1.25 * len(pids)),
        sharex=True,  # fudge to keep proportions about right
    )

    for idx, pid in enumerate(pids):
        person_data = df.loc[df.pid == pid]
        label_x, label_y, labels = [], [], []

        if len(pids) == 1:
            ax = axs
        else:
            ax = axs[idx]

        for i in range(len(person_data)):
            y = 1
            data = person_data.iloc[i]
            ax.barh(
                y,
                width="dur",
                data=data,
                left="start_time",
                label="act",
                color="color",
                edgecolor="black",
                linewidth=2,
            )

            # Populate Labelling Params
            label_x.append(data["start_time"] + data["dur"] / 2)
            label_y.append(y)
            labels.append(data.act)

        # Labels
        rects = ax.patches

        for x, y, rect, label in zip(label_x, label_y, rects, labels):
            r, g, b, _ = rect.get_facecolor()
            # see https://en.wikipedia.org/wiki/Relative_luminance
            luminance = (r * 0.2126 + g * 0.7152 + b * 0.0722) * 255
            if luminance < 140:
                color = "white"
            else:
                color = "black"
            if isinstance(label_fontsize, dict):
                _fontsize = label_fontsize.get(label, scaled_fontsize)
            elif label_fontsize is not None:
                _fontsize = label_fontsize
            else:
                _fontsize = scaled_fontsize

            scaled_rect_width = rect.get_width() * width / DEFAULT_ACTIVITIES_PLOT_WIDTH

            if scaled_rect_width >= 2:
                ax.text(
                    x,
                    y,
                    label,
                    ha="center",
                    va="center",
                    fontdict={"color": color, "size": _fontsize, "weight": "regular"},
                )
            elif scaled_rect_width >= 0.5:
                ax.text(
                    x,
                    y,
                    label,
                    ha="center",
                    va="center",
                    fontdict={
                        "color": color,
                        "size": _fontsize,
                        "weight": "regular",
                        "rotation": 90,
                    },
                )

        ax.set_title(f"Person ID: {pid}", fontsize=scaled_fontsize)
        ax.get_yaxis().set_visible(False)
        ax.set_xticks(range(25))
        ax.set_xlim(right=24)
        ax.tick_params(axis="x", which="major", labelsize=scaled_fontsize)
        for side in ["top", "right", "bottom", "left"]:
            ax.spines[side].set_visible(False)

    if legend:
        legend_elements = []
        for act, color in cmap.items():
            legend_elements.append(Patch(facecolor=color, edgecolor="black", label=act))
        fig.legend(
            handles=legend_elements,
            ncol=len(legend_elements),
            prop={"size": 1.2 * scaled_fontsize},
            frameon=False,
            bbox_to_anchor=(0.5, 0),
            loc="upper center",
            borderaxespad=0.0,
            borderpad=0.5,
        )
    fig.tight_layout()

    if path is not None:
        fig.savefig(path, bbox_inches="tight")

    return fig, axs


def plot_travel_plans(
    gdf: GeoDataFrame,
    groupby: Optional[list] = None,
    colour_by: str = "mode",
    cmap: Optional[dict] = None,
    mapbox_access_token: str = "",
) -> go.Figure:
    """Uses plotly's Scattermapbox to plot travel GeoDataFrame.

    Args:
      gdf (GeoDataFrame): Ouptut of `build_person_travel_geodataframe`.
      groupby (list, optional): List of column names to group together into different plotly `traces`. Defaults to None.
      colour_by (str, optional): The `gdf` column that should be used to define colours in the plot. Defaults to "mode".
      cmap (dict, optional): Useful to pass if generating a number of plots and want to keep colour scheme. Defaults to None.
      mapbox_access_token (str, optional):
        required to generate the plot. See https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
        Defaults to "".
    Returns:
        go.Figure: plotly figure object

    """
    if not mapbox_access_token:
        raise Warning("You need to pass `mapbox_access_token` for the plot to appear.")
    _gdf = gdf.copy()
    _gdf["start_time"] = _gdf["start_time"].dt.strftime("%H:%M:%S")
    _gdf["end_time"] = _gdf["end_time"].dt.strftime("%H:%M:%S")
    _gdf["seq"] = _gdf["seq"].astype(int)

    if cmap is None:
        cmap = build_rgb_travel_cmap(gdf, colour_by)

    data = []
    all_coords = []

    if groupby is None:
        groupby = []
        to_group = colour_by
    else:
        to_group = [colour_by] + groupby
    for name, group in _gdf.groupby(to_group):
        if len(groupby) > 0:
            colour_by_item = name[0]
        else:
            colour_by_item = name
        colour = "rgb({},{},{})".format(
            cmap[colour_by_item][0], cmap[colour_by_item][1], cmap[colour_by_item][2]
        )

        lat = []
        lon = []
        hovertext = []
        for idx in group.index:
            coords = group.loc[idx, "geometry"].coords
            all_coords.extend(coords)
            lat = lat + [point[1] for point in coords] + [float("nan")]
            lon = lon + [point[0] for point in coords] + [float("nan")]
            _hovertext = [""] * (len(coords) + 1)
            _hovertext[0] = "pid: {}<br>start time: {}<br>trip seq: {}<br>mode: {}".format(
                group.loc[idx, "pid"],
                group.loc[idx, "start_time"],
                group.loc[idx, "seq"],
                group.loc[idx, "mode"],
            )
            _hovertext[-2] = "pid: {}<br>end time: {}<br>trip seq: {}<br>mode: {}".format(
                group.loc[idx, "pid"],
                group.loc[idx, "end_time"],
                group.loc[idx, "seq"],
                group.loc[idx, "mode"],
            )
            hovertext = hovertext + _hovertext

        data.append(
            go.Scattermapbox(
                lat=lat,
                lon=lon,
                hovertext=hovertext,
                hoverinfo="text",
                mode="lines+markers",
                marker=dict(size=10, color=colour, opacity=0.75),
                line=dict(color=colour),
                name="{}".format(name),
            )
        )

    if all_coords:
        c_lat = sum([point[1] for point in all_coords]) / len(all_coords)
        c_lon = sum([point[0] for point in all_coords]) / len(all_coords)
    else:
        c_lat = 0
        c_lon = 0

    layout = go.Layout(
        title="",
        autosize=True,
        hovermode="closest",
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(lat=c_lat, lon=c_lon),
            pitch=0,
            zoom=10,
            style="dark",
        ),
    )
    fig = go.Figure(data=data, layout=layout)
    return fig


def plot_activity_breakdown_area(
    plans: list[Plan],
    activity_classes: Optional[list[str]] = None,
    plans_encoder: Optional[type[encoder.PlanEncoder]] = None,
    normalize: bool = False,
    legend: bool = True,
    ax: Optional[plt.Axes] = None,
    colormap: str = "tab20",
) -> plt.Axes:
    """
    Area plot of the breakdown of activities taking place every minute.

    Args:
        plans (list[Plan]): A list of PAM plans.
        activity_classes (Optional[list[str]], optional): A list of the activity labels to encode a plan from. Defaults to None.
        plans_encoder (Optional[type[encoder.PlanEncoder]], optional): A pre-encoded plan; alternative to passing `activity_classes`. Defaults to None.
        normalize (bool, optional): Whether to convert the y-axis to percentages. Defaults to False.
        legend (bool, optional): Whether to include the legend of activities in the plot. Defaults to True.
        ax (Optional[plt.Axes], optional): A matplotlib axis; if not given, a new one will be generated. Defaults to None.
        colormap (str, optional): The colormap to use in the plot. Defaults to "tab20".

    Raises:
        ValueError: One of `activity_classes` or `plans_encoder` must be defined.

    Returns:
        plt.Axes: plot object.
    """
    if activity_classes is not None:
        plans_encoder = encoder.PlansOneHotEncoder(activity_classes=activity_classes)
    elif plans_encoder is None:
        raise ValueError("Please provide a list of activity classes or a plans encoder.")

    labels = plans_encoder.plan_encoder.activity_encoder.labels
    freqs = plans_encoder.encode(plans).sum(axis=0)

    if normalize:
        freqs = freqs.astype(float) / freqs.sum(0)

    if ax is None:
        fig, ax = plt.subplots(1, 1)

    n_labels = len(labels)
    cmap = matplotlib.colormaps[colormap]
    colors = [cmap(x) for x in range(n_labels)]

    ax.stackplot(range(freqs.shape[1]), *freqs, colors=colors)

    if legend:
        ax.legend(labels, loc="lower left", bbox_to_anchor=(1.0, 0), frameon=False)

    if normalize:
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: "{:.0%}".format(x)))

    ax.set_xlim(0, freqs.shape[1])
    ax.set_ylim(0, freqs.sum(0).max())

    return ax


def plot_activity_breakdown_area_tiles(
    plans: dict[list[Plan]], activity_classes: list[str], figsize=(10, 8), **kwargs
):
    """Tiled area plot of the breakdown of activities taking place every minute."""
    plans_encoder = encoder.PlansOneHotEncoder(activity_classes=activity_classes)
    labels = plans_encoder.plan_encoder.activity_encoder.labels
    nrows = int(np.ceil(len(plans) / 2))
    irow = 0
    icol = 0
    fig, axs = plt.subplots(nrows, 2, figsize=figsize, sharex=True, sharey=True)
    fig.tight_layout(pad=2)
    for k, v in plans.items():
        n = len(v)
        if nrows > 1:
            ax = axs[irow, icol]
        else:
            ax = axs[icol]
        print(ax)
        plot_activity_breakdown_area(
            plans=v, ax=ax, legend=False, normalize=True, plans_encoder=plans_encoder, **kwargs
        )
        ax.set_title(f"Cluster {k} - {n} plans")
        irow += icol
        icol = (icol + 1) % 2

    ax.legend(labels, loc="lower left", bbox_to_anchor=(1.0, 0), frameon=False)

    return axs
