from datetime import timedelta

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from pam.utils import dt_to_s, td_to_s


def extract_activity_log(population):
    log = []
    for hid, pid, person in population.people():
        for activity in person.activities:
            log.append(
                {
                    "act": activity.act,
                    "start": dt_to_s(activity.start_time),
                    "end": dt_to_s(activity.end_time),
                    "duration": td_to_s(activity.duration),
                }
            )

    return pd.DataFrame(log)


def extract_leg_log(population):
    log = []
    for hid, pid, person in population.people():
        for leg in person.legs:
            log.append(
                {
                    "mode": leg.mode,
                    "start": dt_to_s(leg.start_time),
                    "end": dt_to_s(leg.end_time),
                    "duration": td_to_s(leg.duration),
                }
            )

    return pd.DataFrame(log)


def time_binner(data):
    """Bin start and end times and durations, return freq table for 24 hour period, 15min intervals."""
    bins = list(range(0, 24 * 60 * 60 + 1, 15 * 60))
    bins[-1] = 100 * 60 * 60
    labels = pd.timedelta_range(start="00:00:00", periods=96, freq="15min")
    binned = pd.DataFrame(index=pd.timedelta_range(start="00:00:00", periods=96, freq="15min"))
    binned["duration"] = pd.cut(data.duration, bins, labels=labels, right=False).value_counts()
    binned["end"] = pd.cut(data.end, bins, labels=labels, right=False).value_counts()
    binned["start"] = pd.cut(data.start, bins, labels=labels, right=False).value_counts()
    binned = binned / binned.max()
    return binned


def plot_time_bins(data, sub_col, width=12, height_factor=1.2):
    subs = set(data[sub_col])
    fig, axs = plt.subplots(len(subs), figsize=(width, 1.2 * len(subs)), sharex=False)
    if not isinstance(axs, np.ndarray):
        axs = [axs]

    for ax, sub in zip(axs, subs):
        binned = time_binner(data.loc[data[sub_col] == sub])
        ax.pcolormesh(binned.T, cmap="cool", edgecolors="white", linewidth=1)
        ax.xaxis.set_ticks([i for i in range(0, 97, 8)])
        ax.xaxis.set_ticklabels([f"{h:02}:00" for h in range(0, 25, 2)])
        ax.yaxis.set_ticks([0.5, 1.5, 2.5])
        ax.yaxis.set_ticklabels(["Duration", "End time", "Start time"])
        ax.grid(which="minor", color="w", linestyle="-", linewidth=2)
        for pos in ["right", "top", "bottom", "left"]:
            ax.spines[pos].set_visible(False)
        ax.set_title(sub.title(), fontsize="medium", rotation=0)
    fig.tight_layout()
    return fig


def plot_activity_times(population):
    acts = extract_activity_log(population)
    fig = plot_time_bins(acts, sub_col="act")
    return fig


def plot_leg_times(population):
    legs = extract_leg_log(population)
    fig = plot_time_bins(legs, sub_col="mode")
    return fig


def calculate_leg_duration_by_mode(population):
    all_legs = []
    for hid, pid, person in population.people():
        for seq, leg in enumerate(person.legs):
            all_legs.append(
                {
                    "leg mode": leg.mode,
                    "duration_hours": leg.duration.days * 24 + leg.duration.seconds / 3600,
                }
            )
    all_legs_df = pd.DataFrame(all_legs)
    outputs_df = all_legs_df.groupby("leg mode", as_index=False).agg({"duration_hours": "sum"})
    outputs_df.insert(0, "scenario", population.name, True)
    return outputs_df


def calculate_activity_duration_by_act(population, exclude=None):
    all_activities = []
    for hid, pid, person in population.people():
        for seq, activity in enumerate(person.activities):
            all_activities.append(
                {
                    "act": activity.act,
                    "duration_hours": activity.duration.days * 24
                    + activity.duration.seconds / 3600,
                }
            )
    all_activities_df = pd.DataFrame(all_activities)
    outputs_df = all_activities_df.groupby("act", as_index=False).agg({"duration_hours": "sum"})
    outputs_df.insert(0, "scenario", population.name, True)
    if exclude is not None:
        outputs_df = outputs_df[outputs_df.act != exclude]
    return outputs_df


def calculate_total_activity_duration(population, exclude=None):
    total_activity_duration = timedelta(minutes=0)
    for hid, pid, person in population.people():
        for seq, activity in enumerate(person.activities):
            if activity.act != exclude:
                total_activity_duration = total_activity_duration + activity.duration
    total_activity_duration_hours = (
        total_activity_duration.days * 24 + total_activity_duration.seconds / 3600
    )
    return total_activity_duration_hours


def calculate_total_leg_duration(population):
    total_leg_duration = timedelta(minutes=0)
    for hid, pid, person in population.people():
        for seq, leg in enumerate(person.legs):
            total_leg_duration = total_leg_duration + leg.duration
    total_leg_duration_hours = total_leg_duration.days * 24 + total_leg_duration.seconds / 3600
    return total_leg_duration_hours


def plot_activity_duration(list_of_populations, exclude=None, axis=None):
    x = []
    y = []
    for idx, population in enumerate(list_of_populations):
        x.append(population.name)
        y.append(calculate_total_activity_duration(population, exclude))

    outputs_df = pd.DataFrame({"scenario": x, "activity duration (hours)": y})
    x_label_rotation = 90
    if exclude is not None:
        title = "activities (excl " + exclude + ")"
    else:
        title = "activities"

    if axis is None:
        plt.bar(x, y)
        plt.xticks(rotation=x_label_rotation)
        plt.ylabel("duration (hours)")
        plt.title(title)
        plt.show

    else:
        axis.bar(x, y)
        axis.plot()
        axis.set_title(title)
        axis.xaxis.set_label("")
        axis.xaxis.set_ticks(x)
        axis.xaxis.set_ticklabels(x, rotation=x_label_rotation)
    return outputs_df


def plot_leg_duration(list_of_populations, axis=None):
    x = []
    y = []
    for idx, population in enumerate(list_of_populations):
        x.append(population.name)
        y.append(calculate_total_leg_duration(population))

    outputs_df = pd.DataFrame({"scenario": x, "leg duration (hours)": y})
    title = "legs"
    x_label_rotation = 90
    if axis is None:
        plt.bar(x, y)
        plt.xticks(rotation=x_label_rotation)
        plt.ylabel("duration (hours)")
        plt.title(title)
    else:
        axis.bar(x, y)
        axis.plot()
        axis.set_title(title)
        axis.xaxis.set_label("")
        axis.xaxis.set_ticks(x)
        axis.xaxis.set_ticklabels(x, rotation=x_label_rotation)
    return outputs_df


def plot_activity_duration_by_act(list_of_populations, exclude=None, axis=None):
    population_act_df = pd.DataFrame()
    for idx, population in enumerate(list_of_populations):
        population_act_df = pd.concat(
            [population_act_df, calculate_activity_duration_by_act(population, exclude)],
            ignore_index=True,
        )
    pivot_for_chart = population_act_df.pivot(
        index="scenario", columns="act", values="duration_hours"
    )

    if exclude is not None:
        title = "activities by type (excl " + exclude + ")"
    else:
        title = "activities by type"

    if axis is None:
        pivot_for_chart.plot.bar(stacked=True)
        plt.ylabel("duration (hours)")
        plt.title(title)
        plt.show
    else:
        pivot_for_chart.plot.bar(stacked=True, ax=axis)
        axis.set_xlabel("")
        axis.set_title(title)
    return pivot_for_chart


def plot_leg_duration_by_mode(list_of_populations, axis=None):
    population_mode_df = pd.DataFrame()
    for idx, population in enumerate(list_of_populations):
        population_mode_df = pd.concat(
            [population_mode_df, calculate_leg_duration_by_mode(population)], ignore_index=True
        )
    pivot_for_chart = population_mode_df.pivot(
        index="scenario", columns="leg mode", values="duration_hours"
    )
    title = "legs by mode"

    if axis is None:
        pivot_for_chart.plot.bar(stacked=True)
        plt.title(title)
        plt.ylabel("duration (hours)")
    else:
        pivot_for_chart.plot.bar(stacked=True, ax=axis)
        axis.set_xlabel("")
        axis.set_title(title)
    return pivot_for_chart


def plot_population_comparisons(list_of_populations, activity_to_exclude=None):
    fig1, ax = plt.subplots(nrows=1, ncols=2, tight_layout=True, sharey=True)
    plot_leg_duration(list_of_populations, ax[0])
    leg_modes = plot_leg_duration_by_mode(list_of_populations, ax[1])
    ax[0].set_ylabel("duration (hours)")

    fig2, ax2 = plt.subplots(nrows=1, ncols=2, tight_layout=True, sharey=True)
    plot_activity_duration(list_of_populations, activity_to_exclude, ax2[0])
    activity_types = plot_activity_duration_by_act(list_of_populations, activity_to_exclude, ax2[1])
    ax2[0].set_ylabel("duration (hours)")

    leg_modes["TOTAL"] = leg_modes.sum(axis=1)
    activity_types["TOTAL"] = activity_types.sum(axis=1)
    print(leg_modes, "\n", activity_types)

    return fig1, fig2, leg_modes, activity_types
