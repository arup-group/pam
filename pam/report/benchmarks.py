from typing import Callable, List, Optional

import pandas as pd


def benchmarks(population):
    """Yield bms.

    :param pam.core.Population population: pam.core.Population
    :yield pandas.DataFrame: benchmark
    """
    bms = [
        (
            "mode_counts.csv",
            {
                "dimensions": ["mode"],
                "data_fields": ["freq"],
                "colnames": ["mode", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "distances.csv",
            {
                "dimensions": ["euclidean_distance_category"],
                "data_fields": ["freq"],
                "colnames": ["distance", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "mode_distances.csv",
            {
                "dimensions": ["mode", "euclidean_distance_category"],
                "data_fields": ["freq"],
                "colnames": ["mode", "distance", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "durations.csv",
            {
                "dimensions": ["duration_category"],
                "data_fields": ["freq"],
                "colnames": ["duration", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "mode_durations.csv",
            {
                "dimensions": ["mode", "duration_category"],
                "data_fields": ["freq"],
                "colnames": ["mode", "duration", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "departure_times.csv",
            {
                "dimensions": ["departure_hour"],
                "data_fields": ["freq"],
                "colnames": ["departure_hour", "trips"],
                "aggfunc": [sum],
            },
        ),
        (
            "mode_purposes.csv",
            {
                "dimensions": ["mode", "purp"],
                "data_fields": ["freq"],
                "colnames": ["mode", "purpose", "trips"],
                "aggfunc": [sum],
            },
        ),
    ]
    trips = population.trips_df()
    for path, kwargs in bms:
        yield path, create_benchmark(trips.copy(), **kwargs)


def create_benchmark(
    data,
    dimensions: Optional[List[str]] = None,
    data_fields: Optional[List[str]] = None,
    aggfunc: List[Callable] = [len],
    normalise_by=None,
    colnames=None,
):
    """Extract user-specified benchmarks from the population
    :param pandas.DataFrame data: dataframe of trip or leg logs with required fields
    :param list dimensions: Dimensions to group by. If None, return the disaggregate dataset
    :params list data_fields: The data to summarise. If None, simply count the instances of each group
    :params list of functions aggfunc: A set of functions to apply to each data_field, after grouping by the specified dimensions. For example: [len, sum], [sum, np.mean], [np.sum], etc
    :params list normalise_by: convert calculated values to percentages across the specified -by this field- dimension(s)
    :params list colnames: if different to None, rename the columns of the returned dataset.

    :return: pandas.DataFrame
    """
    df = data.copy()

    ## aggregate across specified dimensions
    if dimensions is not None:
        if data_fields is not None:
            df = df.groupby(dimensions)[data_fields].agg(aggfunc).fillna(0)
        else:
            df = df.value_counts(dimensions)

    ## show as percentages
    if normalise_by is not None:
        if normalise_by == "total":
            df = df / df.sum(axis=0)
        else:
            df = df.groupby(level=normalise_by).transform(lambda x: x / x.sum())
    df = df.sort_index().reset_index()

    ## flatten column MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.map("_".join).str.strip("_")

    ## rename columns
    if colnames is not None:
        df.columns = colnames

    return df


#### benchmark wrappers:
def mode_counts(population):
    # number of trips by (euclidean) distance category
    data = population.trips_df()
    return create_benchmark(
        data, dimensions=["mode"], data_fields=["freq"], colnames=["mode", "trips"], aggfunc=[sum]
    )


def distance_counts(population):
    # number of trips by (euclidean) distance category
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["euclidean_distance_category"],
        data_fields=["freq"],
        colnames=["distance", "trips"],
        aggfunc=[sum],
    )


def mode_distance_counts(population):
    # number of trips by (euclidean) distance category and mode
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["mode", "euclidean_distance_category"],
        data_fields=["freq"],
        colnames=["mode", "distance", "trips"],
        aggfunc=[sum],
    )


def duration_counts(population):
    # number of trips by duration
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["duration_category"],
        data_fields=["freq"],
        colnames=["duration", "trips"],
        aggfunc=[sum],
    )


def mode_duration_counts(population):
    # number of trips by duration and mode
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["mode", "duration_category"],
        data_fields=["freq"],
        colnames=["mode", "duration", "trips"],
        aggfunc=[sum],
    )


def departure_time_counts(population):
    # number of trips by hour of departure
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["departure_hour"],
        data_fields=["freq"],
        colnames=["departure_hour", "trips"],
        aggfunc=[sum],
    )


def mode_purpose_counts(population):
    # purpose split for each mode
    data = population.trips_df()
    return create_benchmark(
        data,
        dimensions=["mode", "purp"],
        data_fields=["freq"],
        colnames=["mode", "purpose", "trips"],
        aggfunc=[sum],
    )
