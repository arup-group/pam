import pandas as pd
from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
import plotly.graph_objs as go
from plotly.offline import offline
import pam.activity as activity
import pam.utils as utils


def plot_person(person, **kwargs):
    df = build_person_df(person)
    plot_activities(df, **kwargs)


def plot_persons(persons, kwargs=None):
    df = pd.concat([build_person_df(person) for person in persons])
    plot_activities(df, **kwargs)


def plot_household(household, **kwargs):
    df = pd.concat([build_person_df(person) for person in household.people.values()])
    plot_activities(df, **kwargs)

def build_plan_df(plan, pid='sample'):
    """
    Loop through a plan, creating a pandas dataframe defining activities for plotting.
    """
    data = {
        "act" : [],
        "modes": [],
        "start_time": [],
        "end_time": [],
        "dur": [],
    }
    for component in plan.day:
        data["act"].append(component.act.lower().title())
        if isinstance(component, activity.Leg):
            data["modes"].append(component.mode.lower().title())
        else:
            data["modes"].append(None)
        data["start_time"].append(component.start_time.hour + component.start_time.minute/60)
        data["end_time"].append(component.end_time.hour + component.end_time.minute/60)
        data["dur"].append(component.duration.total_seconds()/3600)
    df = pd.DataFrame(data)
    df['pid'] = pid

    return df

def plot_plan(plan, kwargs=None):
    df = build_plan_df(plan)
    if kwargs is not None:
        plot_activities(df, **kwargs)
    else:
        plot_activities(df)


def build_person_df(person):
    """
    Loop through a persons plan, creating a pandas dataframe defining activities for plotting.
    """
    data = {
        "act" : [],
        "modes": [],
        "start_time": [],
        "end_time": [],
        "dur": [],
    }
    for component in person.plan.day:
        data["act"].append(component.act.lower().title())
        if isinstance(component, activity.Leg):
            data["modes"].append(component.mode.lower().title())
        else:
            data["modes"].append(None)
        data["start_time"].append(component.start_time.hour + component.start_time.minute/60)
        data["end_time"].append(component.end_time.hour + component.end_time.minute/60)
        data["dur"].append(component.duration.total_seconds()/3600)
    df = pd.DataFrame(data)
    df['pid'] = person.pid

    return df


def build_person_travel_geodataframe(person, from_epsg=None, to_epsg=None):
    """
    Loop through a persons legs, creating a geopandas GeoDataFrame defining travel for plotting.
    :param person: pam.core.Person object
    :param from_epsg: coordinate system the plans are currently in, optional
    :param to_epsg: coordinate system you want the geo dataframe to be projected to, optional, you need to specify
    from_epsg as well to use this.
    :return:
    """
    df = pd.DataFrame()
    for leg in person.legs:
        if (leg.start_location.loc is None) or (leg.end_location.loc is None):
            raise AttributeError('To create a geopandas.DataFrame you need specific locations. Make sure Legs have'
                                 'loc attribute defined with a shapely.Point or s2sphere.CellId.')
        _leg_dict = leg.__dict__.copy()
        _leg_dict['geometry'] = utils.get_linestring(leg.start_location.loc, leg.end_location.loc)
        coords = list(_leg_dict['geometry'].coords)
        _leg_dict['start_location'] = coords[0]
        _leg_dict['end_location'] = coords[-1]
        df = df.append(pd.Series(_leg_dict), ignore_index=True)

    df['pid'] = person.pid
    df = GeoDataFrame(df, geometry='geometry')
    if from_epsg:
        df.crs = from_epsg
        if to_epsg:
            df = df.to_crs(to_epsg)

    return df


def build_rgb_travel_cmap(df, colour_by):
    colors = [(int(tup[0]*255), int(tup[1]*255), int(tup[2]*255)) for tup in plt.cm.Set3.colors[::-1]]
    colour_by_unique = df[colour_by].unique()
    # repeat colours if unique items > 12
    len_factor = (len(colour_by_unique) // len(colors)) + 1
    d_color = dict(zip(colour_by_unique, colors*len_factor))
    return d_color


def build_cmap(df):
    colors = plt.cm.Set3.colors[::-1]
    activities_unique = df['act'].unique()
    # repeat colours if unique items > 1
    len_factor = (len(activities_unique) // len(colors)) + 1
    d_color = dict(zip(activities_unique, colors*len_factor))
    d_color['Travel'] = (.3,.3,.3)
    return d_color


def plot_activities(df, **kwargs):
    """
    Plot activity plans from pandas dataframe.
    """
    if "cmap" not in kwargs:
        cmap = build_cmap(df)
    else:
        cmap=kwargs["cmap"]

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

    if kwargs.get("legend", True) == True:
        legend_elements = []
        for act, color in cmap.items():
            legend_elements.append(
                Patch(facecolor=color, edgecolor='black', label=act)
            )
        plt.legend(
            handles=legend_elements, ncol=len(legend_elements),
            prop={'size':12}, frameon=False,
            bbox_to_anchor=(.5, -.5), loc='upper center', borderaxespad=0.
            )
            
    plt.xticks(range(25))
    plt.xlim(right=24)

    plt.tight_layout()

    if kwargs.get("path") is not None:
        plt.savefig(kwargs["path"])


def plot_travel_plans(gdf, groupby: list = None, colour_by: str = 'mode', cmap: dict = None,
                      mapbox_access_token: str = ''):
    """
    Uses plotly's Scattermapbox to plot travel GeoDataFrame
    :param gdf: geopandas.GeoDataFrame generated by build_person_travel_geodataframe
    :param groupby: optional argument for splitting traces in the plot
    :param colour_by: argument for specifying what the colour should correspond to in the plot, travel mode by default
    :param cmap: optional argument, useful to pass if generating a number of plots and want to keep colour scheme
    consistent
    :param mapbox_access_token: required to generate the plot
    https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
    :return:
    """
    if not mapbox_access_token:
        raise Warning('You need to pass `mapbox_access_token` for the plot to appear.')
    _gdf = gdf.copy()
    _gdf['start_time'] = _gdf['start_time'].dt.strftime('%H:%M:%S')
    _gdf['end_time'] = _gdf['end_time'].dt.strftime('%H:%M:%S')
    _gdf['seq'] = _gdf['seq'].astype(int)

    if cmap is None:
        cmap = build_rgb_travel_cmap(gdf, colour_by)

    data = []
    all_coords = []

    if groupby is None:
        groupby = []
    for name, group in _gdf.groupby([colour_by] + groupby):
        if len(groupby) > 0:
            colour_by_item = name[0]
        else:
            colour_by_item = name
        colour = 'rgb({},{},{})'.format(cmap[colour_by_item][0], cmap[colour_by_item][1], cmap[colour_by_item][2])

        lat = []
        lon = []
        hovertext = []
        for idx in group.index:
            coords = group.loc[idx, 'geometry'].coords
            all_coords.extend(coords)
            lat = lat + [point[1] for point in coords] + [float('nan')]
            lon = lon + [point[0] for point in coords] + [float('nan')]
            _hovertext = [''] * (len(coords) + 1)
            _hovertext[0] = 'pid: {}<br>start time: {}<br>trip seq: {}<br>mode: {}'.format(
                group.loc[idx, 'pid'], group.loc[idx, 'start_time'], group.loc[idx, 'seq'], group.loc[idx, 'mode'])
            _hovertext[-2] = 'pid: {}<br>end time: {}<br>trip seq: {}<br>mode: {}'.format(
                group.loc[idx, 'pid'], group.loc[idx, 'end_time'], group.loc[idx, 'seq'], group.loc[idx, 'mode'])
            hovertext = hovertext + _hovertext

        data.append(go.Scattermapbox(
            lat=lat,
            lon=lon,
            hovertext=hovertext,
            hoverinfo='text',
            mode='lines+markers',
            marker=dict(
                size=10,
                color=colour,
                opacity=0.75
            ),
            line=dict(
                color=colour
            ),
            name='{}'.format(name)
        ))

    if all_coords:
        c_lat = sum([point[1] for point in all_coords]) / len(all_coords)
        c_lon = sum([point[0] for point in all_coords]) / len(all_coords)
    else:
        c_lat = 0
        c_lon = 0

    layout = go.Layout(
        title='',
        autosize=True,
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=c_lat,
                lon=c_lon
            ),
            pitch=0,
            zoom=10,
            style='dark'
        )
    )
    fig = go.Figure(data=data, layout=layout)
    return fig
