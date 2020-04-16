import pandas as pd

from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt


def load_travel_diary(trips_df, attributes_df):

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
                    start_time=mtdt(0),
                )
            )

            for n in range(0,len(trips)):
                trip = trips.iloc[n]

                destination_activity = trip.purp
                destination_activity_previous = trips.iloc[n-1].purp if n>0 else None # destination activity one leg back
                destination_activity_next = trips.iloc[n+1].purp if n<len(trips)-1 else None # destination activity one leg forward 

                person.add(
                    Leg(
                        seq=n,
                        mode=trip['mode'],
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=mtdt(trip.tst),
                        end_time=mtdt(trip.tet)
                    )
                )

                if n==(len(trips)-1):
                    # the last activity needs to be either home or work
                    person.add(
                        Activity(
                            seq=n,
                            act='home' if trip.hzone==trip.dzone else 'work',
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )
                elif destination_activity == destination_activity_previous:
                    # a return trip ends in a home or work activity
                    person.add(
                        Activity(
                            seq=n,
                            act='home' if trip.hzone==trip.dzone else 'work',
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )
                elif destination_activity == destination_activity_next:
                    # either in the middle of a return trip or in home
                    person.add(
                        Activity(
                            seq=n,
                            act='home' if trip.hzone==trip.dzone else trip.purp,
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )
                else:
                    person.add(
                        Activity(
                            seq=n,
                            act=trip.purp,
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )




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
