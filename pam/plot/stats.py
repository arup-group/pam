import pandas as pd
from matplotlib import pyplot as plt

from pam.utils import dt_to_s, td_to_s


def extract_activity_log(population):
    log = []
    for hid, pid, person in population.people():
        for activity in person.activities:
            log.append({
                'act': activity.act,
                'start': dt_to_s(activity.start_time),
                'end': dt_to_s(activity.end_time),
                'duration': td_to_s(activity.duration)
            })

    return pd.DataFrame(log)


def extract_leg_log(population):
    log = []
    for hid, pid, person in population.people():
        for leg in person.legs:
            log.append({
                'mode': leg.mode,
                'start': dt_to_s(leg.start_time),
                'end': dt_to_s(leg.end_time),
                'duration': td_to_s(leg.duration)
            })

    return pd.DataFrame(log)


def time_binner(data):
    """
    Bin start and end times and durations, return freq table for 24 hour period, 15min intervals.
    """
    bins = list(range(0, 24*60*60+1, 15*60))
    bins[-1] = 100*60*60
    labels = pd.timedelta_range(start='00:00:00', periods=96, freq='15min')  
    binned = pd.DataFrame(index=pd.timedelta_range(start='00:00:00', periods=96, freq='15min'))
    binned['duration'] = pd.cut(data.duration, bins, labels=labels, right=False).value_counts()
    binned['end'] = pd.cut(data.end, bins, labels=labels, right=False).value_counts()
    binned['start'] = pd.cut(data.start, bins, labels=labels, right=False).value_counts()
    binned = binned / binned.max()
    return binned


def plot_time_bins(data, sub_col):
    
    subs = set(data[sub_col])
    fig, axs = plt.subplots(len(subs), figsize=(12, len(subs)), sharex=True)
    
    for ax, sub in zip(axs, subs):

        binned = time_binner(data.loc[data[sub_col] == sub])
        ax.pcolormesh(binned.T, cmap='cool', edgecolors='white', linewidth=1)

        ax.set_xticks([i for i in range(0,97,8)])
        ax.set_xticklabels([f"{h:02}:00" for h in range(0,25,2)])
        ax.set_yticks([0.5,1.5,2.5])
        ax.set_yticklabels(['Duration', 'End time', 'Start time'])
        ax.grid(which='minor', color='w', linestyle='-', linewidth=2)
        for pos in ['right','top','bottom','left']:
            ax.spines[pos].set_visible(False)
        ax.set_ylabel(sub.title(), fontsize='medium')
        
    return fig


def plot_activity_times(population):
    acts = extract_activity_log(population)
    fig = plot_time_bins(acts, sub_col='act')
    fig.suptitle("Activity Time Bins")
    return fig


def plot_leg_times(population):
    legs = extract_leg_log(population)
    fig = plot_time_bins(legs, sub_col='mode')
    fig.suptitle("Travel Time Bins")
    return fig

