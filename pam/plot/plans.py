import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
import pam.activity as activity


def plot_person(person, kwargs=None):
    df = build_person_df(person)
    if kwargs is not None:
        plot_activities(df, **kwargs)
    else:
        plot_activities(df)


def plot_persons(persons, kwargs=None):
    df = pd.concat([build_person_df(person) for person in persons])
    if kwargs is not None:
        plot_activities(df, **kwargs)
    else:
        plot_activities(df)


def plot_household(household, kwargs=None):
    df = pd.concat([build_person_df(person) for person in household.people.values()])
    if kwargs is not None:
        plot_activities(df, **kwargs)
    else:
        plot_activities(df)


def build_person_df(person):
    """
    Loop through a persons plan, creating a pandas dataframe for plotting.
    """
    activities, modes, start_times, end_times, durations = [], [], [], [], []

    for component in person.plan.day:
        activities.append(component.act.lower().title())
        if isinstance(component, activity.Leg):
            modes.append(component.mode.lower().title())
        else:
            modes.append(None)
        start_times.append(component.start_time.hour + component.start_time.minute/60)
        end_times.append(component.end_time.hour + component.end_time.minute/60)
        durations.append(component.duration.total_seconds()/3600)

    df = pd.DataFrame(
        zip(activities, modes, start_times, durations),
        columns=['act', 'mode', 'start_time', 'dur'])
    df['pid'] = person.pid

    return df


def build_cmap(df):
    colors = plt.cm.Set3.colors[::-1]
    activities_unique = df['act'].unique()
    d_color = dict(zip(activities_unique, colors))
    d_color['Travel'] = (.3,.3,.3)
    return d_color


def plot_activities(df, cmap: dict = None, path: str = ''):
    """
    Plot activity plans from pandas dataframe.
    """
    if cmap is None:
        cmap = build_cmap(df)
    df['color'] = df['act'].map(cmap)
    pids = df['pid'].unique()

    fig, axs = plt.subplots(
        len(pids), 1,
        figsize=(
            16,
            3 + (1 * (len(pids)-1))  # fudge to keep proportions about right
            ),
        sharex=True
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
            ax.barh(y, 
                    width='dur', 
                    data=data,
                    left='start_time',
                    label='act',
                    color='color',
                    edgecolor='black',
                    linewidth=2
                )
            
            #Populate Labelling Params
            label_x.append(data['start_time'] + data['dur'] / 2)
            label_y.append(y)
            labels.append(data.act)
    
        # Labels
        rects = ax.patches
        for x, y, rect, label in zip(label_x, label_y, rects, labels):
            if label == 'Travel':
                color = 'white'
            else:
                color = 'black'

            if rect.get_width() >= 2:
                ax.text(x, y, label, ha='center', va='center',
                        fontdict={
                            'color':color, 'size':10, 'weight':'regular'
                            }
                            )
                continue
            if rect.get_width() >= .5:
                ax.text(x, y, label, ha='center', va='center',
                        fontdict={
                            'color':color, 'size':10, 'weight':'regular', 'rotation':90
                            }
                            )

        ax.set_title(f"Person ID: {pid}")
        ax.get_yaxis().set_visible(False)
        for side in ['top', 'right', 'bottom', 'left']:
            ax.spines[side].set_visible(False)

    legend_elements = []
    for act, color in cmap.items():
        legend_elements.append(
            Patch(facecolor=color, edgecolor='black', label=act)
        )
            
    plt.xticks(range(25))
    plt.xlim(right=24)
    plt.legend(
        handles=legend_elements, ncol=len(legend_elements),
        prop={'size':12}, frameon=False,
        bbox_to_anchor=(.5, -.5), loc='upper center', borderaxespad=0.)
    plt.tight_layout()

    if path:
        plt.savefig(path)
