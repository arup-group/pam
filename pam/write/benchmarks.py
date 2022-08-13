import os
import pandas as pd
from typing import Optional, Callable, List


def write_benchmarks(
    population,
    dimensions : Optional[List[str]] = None,
    data_fields : Optional[List[str]] = None,
    aggfunc : List[Callable]= [len],
    normalise_by = None,
    colnames = None,
    path = None
):
    """
    Extract user-specified benchmarks from the population.
    :param pam.core.Population population: PAM population
    :param list dimensions: Dimensions to group by. If None, return the disaggregate dataset
    :params list data_fields: The data to summarise. If None, simply count the instances of each group
    :params list of functions aggfunc: A set of functions to apply to each data_field, after grouping by the specified dimensions. For example: [len, sum], [sum, np.mean], [np.sum], etc
    :params list normalise_by: convert calculated values to percentages across the specified -by this field- dimension(s).
    :params list colnames: if different to None, rename the columns of the returned dataset
    :param str path: directory to write the benchmarks. If None, the functions returns the dataframe instead.

    :return: None if an export path is provided, otherwise Pandas DataFrame
    """
    ## collect data
    df = []
    for hid, pid, person in population.people():
        for seq, leg in enumerate(person.legs):
            record = {
                    'pid': pid,
                    'hid': hid,
                    'hzone': person.home,
                    'ozone': leg.start_location.area,
                    'dzone': leg.end_location.area,
                    'oloc': leg.start_location,
                    'dloc': leg.end_location,
                    'seq': seq,
                    'purp': leg.purp,
                    'mode': leg.mode,
                    'tst': leg.start_time.time(),
                    'tet': leg.end_time.time(),
                    'duration': leg.duration / pd.Timedelta(minutes = 1), #duration in minutes
                    'euclidean_distance': leg.euclidean_distance,
                    'freq': person.freq,
                }
            record = {**record, **dict(person.attributes)} # add person attributes
            df.append(record)
    df = pd.DataFrame(df)

    ## add extra fields used for benchmarking
    df['personhrs'] = df['freq'] * df['duration'] / 60
    df['departure_hour'] = df.tst.apply(lambda x:x.hour)
    df['arrival_hour'] = df.tet.apply(lambda x:x.hour)
    df['euclidean_distance_category'] = pd.cut(
        df.euclidean_distance,
        bins =[0,1,5,10,25,50,100,200,999999],
        labels = ['0 to 1 km', '1 to 5 km', '5 to 10 km', '10 to 25 km', '25 to 50 km', '50 to 100 km', '100 to 200 km', '200+ km']
    )
    df['duration_category'] = pd.cut(
        df.duration,
        bins =[0,5,10,15,30,45,60,90,120,999999],
        labels = ['0 to 5 min', '5 to 10 min', '10 to 15 min', '15 to 30 min', '30 to 45 min', '45 to 60 min', '60 to 90 min', '90 to 120 min', '120+ min']
    )

    ## aggregate across specified dimensions
    if dimensions != None:
        if data_fields != None:
            df = df.groupby(dimensions)[data_fields].agg(aggfunc).fillna(0)
        else:
            df = df.value_counts(dimensions)

    ## show as percentages
    if normalise_by != None:
        if normalise_by == 'total':
            df = df / df.sum(axis = 0)
        else:
            df = df.groupby(level = normalise_by).transform(lambda x: x / x.sum())
    df = df.sort_index().reset_index()

    ## flatten column MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.map('_'.join).str.strip('_')

    ## rename columns
    if colnames != None:
        df.columns = colnames

    ## export or return dataframe
    if path != None:
        if path.lower().endswith('.csv'):
            df.to_csv(path, index=False)
        elif path.lower().endswith('.json'):
            df.to_json(path, orient='records')
        else:
            raise ValueError('Please specify a valid csv or json file path.')

    return df


#### benchmark wrappers:
def write_distance_benchmark(population, path=None):
    # number of trips by (euclidean) distance category
    return write_benchmarks(
        population,
        dimensions = ['euclidean_distance_category'],
        data_fields= ['freq'],
        colnames = ['distance', 'trips'],
        aggfunc = [sum],
        path=path
        )


def write_mode_distance_benchmark(population, path=None):
    # number of trips by (euclidean) distance category and mode
    return write_benchmarks(
        population,
        dimensions = ['mode','euclidean_distance_category'],
        data_fields= ['freq'],
        colnames = ['mode','distance', 'trips'],
        aggfunc = [sum],
        path=path
        )


def write_duration_benchmark(population, path=None):
    # number of trips by duration
    return write_benchmarks(
        population,
        dimensions = ['duration_category'],
        data_fields= ['freq'],
        colnames = ['duration', 'trips'],
        aggfunc = [sum],
        path=path
        )


def write_mode_duration_benchmark(population, path=None):
    # number of trips by duration and mode
    return write_benchmarks(
        population,
        dimensions = ['mode','duration_category'],
        data_fields= ['freq'],
        colnames = ['mode','duration','trips'],
        aggfunc = [sum],
        path=path
        )


def write_departure_time_benchmark(population, path=None):
    # number of trips by hour of departure
    return write_benchmarks(
        population,
        dimensions = ['departure_hour'],
        data_fields= ['freq'],
        colnames = ['departure_hour', 'trips'],
        aggfunc = [sum],
        path=path
        )


def write_mode_purpose_split_benchmark(population, path=None):
    # purpose split for each mode
    return write_benchmarks(
        population,
        dimensions = ['mode','purp'],
        data_fields= ['freq'],
        normalise_by = ['mode'],
        colnames = ['mode','purpose','trips'],
        aggfunc = [sum]
        )


def write_benchmarks_batch(population, path):
    """
    Write a batch of bms to the given directory location.

    Args:
        population (pam.core.Population)
        path (str): destination directory

    Returns:
        List: list of bms
    """
    if not os.path.exists(path):
        os.mkdir(path)

    bms = [
        (write_distance_benchmark, "distance_benchmark.csv"),
        (write_mode_distance_benchmark, "mode_distance_benchmark.csv"),
        (write_duration_benchmark, "duration_benchmark.csv"),
        (write_mode_duration_benchmark, "mode_duration_benchmark.csv"),
        (write_departure_time_benchmark, "departure_time_benchmark.csv"),
        (write_mode_purpose_split_benchmark, "mode_purpose_split_benchmark.csv")
    ]

    return [bm(population, os.path.join(path, name)) for bm, name in bms]
