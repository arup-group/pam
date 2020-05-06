import pandas as pd
from shapely.geometry import Point
from datetime import datetime, timedelta
from lxml import etree as et
import os
import gzip

from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt
from .utils import datetime_to_matsim_time as dttm
from .utils import get_elems, write_xml


def load_travel_diary(trips_df, attributes_df, sample_perc=None, complex=True):
    """
    Turn standard tabular data inputs (travel survey and attributes) into core population
    format.
    :param trips_df: DataFrame
    :param attributes_df: DataFrame
    :param sample_perc: Float. If different to None, it samples the travel population by the corresponding percentage.
    :return: core.Population
    """
    # TODO check for required col headers and give useful error?

    if not isinstance(trips_df, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    if not isinstance(attributes_df, pd.DataFrame):
        raise UserWarning("Unrecognised input for population attributes")

    if sample_perc is not None:
        trips_df = sample_population(trips_df, attributes_df, sample_perc,
                                     weight_col='freq')  # sample the travel population

    if complex:
        return complex_travel_diary_read(trips_df, attributes_df)
    return basic_travel_diary_read(trips_df, attributes_df)


def basic_travel_diary_read(trips_df, attributes_df):
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
                attributes=attributes_df.loc[pid].to_dict(),
                home_area=home_area
            )

            person.add(
                Activity(
                    seq=0,
                    act='home' if home_area == origin_area else 'work',
                    area=origin_area,
                    start_time=mtdt(0),
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
                        start_time=mtdt(trip.tst),
                        end_time=mtdt(trip.tet)
                    )
                )

                if destination_activity in activities and activity_map.get(
                        trip.dzone):  # assume return trip to this activity
                    person.add(
                        Activity(
                            seq=n + 1,
                            act=activity_map[trip.dzone],
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )

                else:
                    person.add(
                        Activity(
                            seq=n + 1,
                            act=trip.purp,
                            area=trip.dzone,
                            start_time=mtdt(trip.tet),
                        )
                    )

                    if trip.dzone not in activity_map:  # update history
                        # only keeping first activity at each location to ensure returns home
                        activity_map[trip.dzone] = trip.purp

                    activities.append(destination_activity)

            household.add(person)

        population.add(household)

    return population


def complex_travel_diary_read(trips_df, attributes_df):
    population = Population()

    for hid, household_data in trips_df.groupby('hid'):

        household = Household(hid)

        for pid, person_data in household_data.groupby('pid'):

            trips = person_data.sort_values('seq')
            # home_area = trips.hzone.iloc[0]
            # origin_area = trips.ozone.iloc[0]
            # activity_map = {home_area: 'home'}
            # activities = ['home', 'work']

            person = Person(
                pid,
                freq=person_data.freq.iloc[0],
                attributes=attributes_df.loc[pid].to_dict(),
                home_area=trips.hzone.iloc[0]
            )

            person.add(
                Activity(
                    seq=0,
                    act=None,
                    area=trips.ozone.iloc[0],
                    start_time=mtdt(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                person.add(
                    Leg(
                        seq=n,
                        mode=trip['mode'],
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=mtdt(trip.tst),
                        end_time=mtdt(trip.tet),
                        purpose=trip.purp
                    )
                )

                person.add(
                    Activity(
                        seq=n + 1,
                        act=None,
                        area=trip.dzone,
                        start_time=mtdt(trip.tet),
                    )
                )

            person.plan.finalise()
            person.plan.infer_activities_from_leg_purpose()

            household.add(person)

        population.add(household)

    return population


def read_matsim(
        plans_path,
        attributes_path,
        weight=1000,
        household_key=None,
        simplify_pt_trips=False,
        autocomplete=True,
        crop=True
):
    """
    Load a MATSim format population into core population format.
    It is possible to maintain the unity of housholds using a household uid in
    the attributes input, ie:
    <attribute class="java.lang.String" name="hid">hh_0001</attribute>
    :param plans: path to matsim format xml
    :param attributes: path to matsim format xml
    :param weight: int
    :param household_key: {str, None}
    :return: Population
    """
    population = Population()

    attributes_map = load_attributes_map(attributes_path)

    for person_id, plan in selected_plans(plans_path):
        attributes = attributes_map[person_id]

        person = Person(person_id, attributes=attributes, freq=weight)

        act_seq = 0
        leg_seq = 0
        arrival_dt = datetime(1900, 1, 1)
        departure_dt = None

        for stage in plan:
            """
            Loop through stages incre incrementing time and extracting attributes.
            """
            if stage.tag in ['act', 'activity']:
                act_seq += 1
                act_type = stage.get('type')

                loc = None
                x, y = stage.get('x'), stage.get('y')
                if x and y:
                    loc = Point(int(float(x)), int(float(y)))

                if act_type == 'pt interaction':
                    departure_dt = arrival_dt + timedelta(
                        seconds=0.)  # todo this seems to be the case in matsim for pt interactions

                else:
                    departure_dt = datetime.strptime(
                        stage.get('end_time', '23:59:59'), '%H:%M:%S'
                    )

                person.add(
                    Activity(
                        seq=act_seq,
                        act=act_type,
                        loc=loc,
                        link=stage.get('link'),
                        area=None,  # todo
                        start_time=arrival_dt,
                        end_time=departure_dt
                    )
                )

            if stage.tag == 'leg':
                leg_seq += 1

                trav_time = stage.get('trav_time')
                if trav_time:
                    h, m, s = trav_time.split(":")
                    leg_duration = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                    arrival_dt = departure_dt + leg_duration
                else:
                    arrival_dt = departure_dt  # todo this assumes 0 duration unless already known

                person.add(
                    Leg(
                        seq=leg_seq,
                        mode=stage.get('mode'),
                        start_loc=None,
                        end_loc=None,
                        start_link=stage.get('start_link'),
                        end_link=stage.get('end_link'),
                        start_area=None,
                        end_area=None,
                        start_time=departure_dt,
                        end_time=arrival_dt,
                    )
                )

        if simplify_pt_trips:
            person.plan.simplify_pt_trips()

        if crop:
            person.plan.crop()

        if autocomplete:
            person.plan.autocomplete_matsim()

        """
        Check if using households, then update population accordingly.
        """
        if household_key and attributes.get(household_key):  # using households
            if population.get(attributes.get(household_key)):  # existing household
                household = population.get(attributes.get(household_key))
                household.add(person)
            else:  # new household
                household = Household(attributes.get(household_key))
                household.add(person)
                population.add(household)
        else:  # not using households, create dummy household
            household = Household(person_id)
            household.add(person)
            population.add(household)

    return population


def load_attributes_map(attributes_path):
    """
    Given path to MATSim attributes input, return dictionary of attributes (as dict)
    """
    attributes_map = {}
    people = get_elems(attributes_path, "object")
    for person in people:
        att_map = {}
        for attribute in person:
            att_map[attribute.get('name')] = attribute.text
        attributes_map[person.get('id')] = att_map

    return attributes_map


def selected_plans(plans_path):
    """
    Given path to MATSim plans input, yield person id and plan for all selected plans.
    """
    for person in get_elems(plans_path, "person"):
        for plan in person:
            if plan.get('selected') == 'yes':
                yield person.get('id'), plan


def sample_population(trips_df, attributes_df, sample_perc, weight_col='freq'):
    """
    Return the trips of a random sample of the travel population.
    We merge the trips and attribute datasets to enable probability weights based on population demographics.

    :params DataFrame trips_df: Trips dataset
    :params DataFrame attributes_df: Population attributes dataset.
    :params float sample_perc: Sampling percentage
    :params string weight_col: The field to use for probability weighting

    :return: Pandas DataFrame, a sampled version of the trips_df dataframe
    """
    sample_pids = trips_df.groupby('pid')[['freq']].sum().join(attributes_df, how='left').sample(frac=sample_perc,
                                                                                                 weights=weight_col).index
    return trips_df[trips_df.pid.isin(sample_pids)]
