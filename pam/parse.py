import pandas as pd

from .core import Population, Household, Person, Activity, Leg, minutes_to_datetime


def load_travel_diary(trips_df, attributes_df):

    # todo deal with attributes_df

    """
    Turn standard tabular data inputs (travel survey and attributes) into core population
    format.
    :param trips_df: DataFrame
    :param attributes_df: DataFrame
    :return: core.Population
    """

    # TODO check for required col headers and give useful error?
    if not isinstance(trips_df, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    # if not isinstance(attributes_df, pd.DataFrame):
    #     raise UserWarning("Unrecognised input for population attributes")

    population = Population()

    for hid, household_data in trips_df.groupby('hid'):

        household = Household(hid)

        for pid, person_data in household_data.groupby('pid'):

            trips = person_data.sort_values('seq')
            home_area = trips.hzone.iloc[0]
            origin_area = trips.ozone.iloc[0]
            activity_map = {home_area: 'home'}
            activities = ['home', 'work']

            person = Person(
                pid,
                freq=person_data.freq.iloc[0],
                attributes=attributes_df.loc[pid].to_dict())

            person.add(
                Activity(
                    seq=0,
                    act='home' if home_area == origin_area else 'work',
                    area=origin_area,
                    start_time=minutes_to_datetime(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                destination_activity = trip.purp

                person.add(
                    Leg(
                        seq=n,
                        mode=trip['mode'],
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=minutes_to_datetime(trip.tst),
                        end_time=minutes_to_datetime(trip.tet)
                    )
                )

                if destination_activity in activities and activity_map.get(
                        trip.dzone):  # assume return trip to this activity
                    person.add(
                        Activity(
                            seq=n + 1,
                            act=activity_map[trip.dzone],
                            area=trip.dzone,
                            start_time=minutes_to_datetime(trip.tet),
                        )
                    )

                else:
                    person.add(
                        Activity(
                            seq=n + 1,
                            act=trip.purp,
                            area=trip.dzone,
                            start_time=minutes_to_datetime(trip.tet),
                        )
                    )

                    if trip.dzone not in activity_map:  # update history
                        # only keeping first activity at each location to ensure returns home
                        activity_map[trip.dzone] = trip.purp

                    activities.append(destination_activity)

            household.add(person)

        population.add(household)

    return population


def write_travel_plan(population):
    """
    Write a core population object to the standard population tabular formats.
    :param population: core.Population
    :return: None
    """
    # todo
    raise NotImplementedError


def load_matsim(plans, attributes=None):
    """
    Load a MATSim format population into core population format.
    :param plans: path to matsim format xml
    :param attributes: path to matsim format xml
    :return: Population
    """
    # todo
    raise NotImplementedError


def write_matsim(population):
    """
    Write a core population object to matsim xml formats.
    :param population: core.Population
    :return: None
    """
    # todo
    raise NotImplementedError


def write_od_matrices(population, type_seg=None, mode_seg=None, time_seg=None):
    """
    Write a core population object to tabular O-D weighted matrices.
    Optionally segment matrices by type of journey (most likelly based on occupation),
    mode and/or time (ie peaks).
    :param population: core.Population
    :param type_seg: segmentation option tbc
    :param mode_seg: segmentation option tbc
    :param time_seg: segmentation option tbc
    :return: None
    """
    # todo
    raise NotImplementedError
