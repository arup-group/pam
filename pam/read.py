import pandas as pd
from shapely.geometry import Point
from datetime import datetime, timedelta
from lxml import etree as et
import os
import gzip
import logging
import pickle
from typing import Union

import pam.core as core
import pam.activity as activity
import pam.utils as utils


def load_travel_diary(
    trip_diary:pd.DataFrame,
    person_attributes:Union[pd.DataFrame,None]=None,
    hh_attributes:Union[pd.DataFrame,None]=None,
    sample_perc:Union[float,None]=None,
    complex:bool=True,
    include_loc:bool=False,
    ):
    """
    Turn standard tabular data inputs (travel survey and attributes) into core population
    format.
    :param trip_diary: DataFrame
    :param person_attributes: DataFrame
    :param hh_attributes: DataFrame
    :param sample_perc: Float. If different to None, it samples the travel population by the corresponding percentage.
    :param complex: bool
    :param include_loc: bool 
    :return: core.Population
    """
    # TODO check for required col headers and give useful error?

    if not isinstance(trip_diary, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    if person_attributes is not None and not isinstance(person_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for person_attributes")

    if hh_attributes is not None and not isinstance(hh_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for hh_attributes")

    if sample_perc is not None:
        trip_diary = sample_population(
            trip_diary,
            sample_perc,
            weight_col='freq'
            )  # sample the travel population

    if complex:
        return complex_travel_diary_read(
            trip_diary,
            person_attributes,
            hh_attributes,
            include_loc
            )
    return basic_travel_diary_read(
        trip_diary,
        person_attributes
        )


def basic_travel_diary_read(trip_diary, attributes_df):
    population = core.Population()

    for hid, household_data in trip_diary.groupby('hid'):

        household = core.Household(hid)

        for pid, person_data in household_data.groupby('pid'):

            trips = person_data.sort_values('seq')
            home_area = trips.hzone.iloc[0]
            origin_area = trips.ozone.iloc[0]
            activity_map = {home_area: 'home'}
            activities = ['home', 'work']

            person = core.Person(
                pid,
                freq=person_data.freq.iloc[0],
                attributes=attributes_df.loc[pid].to_dict(),
                home_area=home_area
            )

            person.add(
                activity.Activity(
                    seq=0,
                    act='home' if home_area == origin_area else 'work',
                    area=origin_area,
                    start_time=utils.minutes_to_datetime(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                destination_activity = trip.purp

                person.add(
                    activity.Leg(
                        seq=n,
                        mode=trip['mode'].lower(),
                        purp=trip.purp.lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=utils.minutes_to_datetime(trip.tst),
                        end_time=utils.minutes_to_datetime(trip.tet)
                    )
                )

                if destination_activity in activities and activity_map.get(
                        trip.dzone):  # assume return trip to this activity
                    person.add(
                        activity.Activity(
                            seq=n + 1,
                            act=activity_map[trip.dzone],
                            area=trip.dzone,
                            start_time=utils.minutes_to_datetime(trip.tet),
                        )
                    )

                else:
                    person.add(
                        activity.Activity(
                            seq=n + 1,
                            act=trip.purp.lower(),
                            area=trip.dzone,
                            start_time=utils.minutes_to_datetime(trip.tet),
                        )
                    )

                    if trip.dzone not in activity_map:  # update history
                        # only keeping first activity at each location to ensure returns home
                        activity_map[trip.dzone] = trip.purp.lower()

                    activities.append(destination_activity)

            person.plan.finalise()
            household.add(person)

        population.add(household)

    return population


def complex_travel_diary_read(
    trip_diary,
    all_person_attributes,
    all_hh_attributes,
    include_loc=False
    ):
    population = core.Population()

    for hid, household_data in trip_diary.groupby('hid'):

        if all_hh_attributes is not None:
            hh_attributes = all_hh_attributes.loc[hid].to_dict()
        else:
            hh_attributes = None

        household = core.Household(hid, attributes=hh_attributes)

        for pid, person_data in household_data.groupby('pid'):

            trips = person_data.sort_values('seq')

            if all_person_attributes is not None:
                person_attributes = all_person_attributes.loc[pid].to_dict()
            else:
                person_attributes = None

            person = core.Person(
                pid,
                freq=person_data.freq.iloc[0],
                attributes=person_attributes,
                home_area=trips.hzone.iloc[0]
                )
            loc = None
            if include_loc:
                loc = trips.start_loc.iloc[0]
            person.add(
                activity.Activity(
                    seq=0,
                    act=None,
                    area=trips.ozone.iloc[0],
                    loc=loc,
                    start_time=utils.minutes_to_datetime(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                start_loc = None
                end_loc = None

                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc

                person.add(
                    activity.Leg(
                        seq=n,
                        purp=trip.purp.lower(),
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.minutes_to_datetime(trip.tst),
                        end_time=utils.minutes_to_datetime(trip.tet),
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=None,
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.minutes_to_datetime(trip.tet),
                    )
                )

            person.plan.finalise()
            person.plan.infer_activities_from_leg_purpose()

            household.add(person)

        population.add(household)

    return population


def load_activity_plan(
    trip_diary:pd.DataFrame,
    person_attributes:Union[pd.DataFrame,None]=None,
    hh_attributes:Union[pd.DataFrame,None]=None,
    sample_perc:Union[float,None]=None,
    ):
    """
    Turn Activity Plan tabular data inputs (derived from travel survey and attributes) into core population
    format. This is a variation of the standard load_travel_diary() method because it does not require
    activity inference. However all plans are expected to be tour based, so assumed to start and end at home.
    We expect broadly the same data schema except rather than trip 'purpose' we use trips 'activity'.
    :param trip_diary: DataFrame
    :param person_attributes: DataFrame
    :param hh_attributes: DataFrame
    :param sample_perc: Float. If different to None, it samples the travel population by the corresponding percentage.
    :return: core.Population
    """
    # TODO check for required col headers and give useful error?

    logger = logging.getLogger(__name__)

    if not isinstance(trip_diary, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    if person_attributes is not None and not isinstance(person_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for population person attributes")

    if hh_attributes is not None and not isinstance(hh_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for population household attributes")

    if sample_perc is not None:
        trip_diary = sample_population(
            trip_diary,
            sample_perc,
            weight_col='freq'
            )  # sample the travel population

    population = core.Population()

    for hid, household_data in trip_diary.groupby('hid'):

        if hh_attributes is not None:
            hh_attribute_dict = hh_attributes.loc[hid].to_dict()
        else:
            hh_attribute_dict = None

        household = core.Household(hid, attributes=hh_attribute_dict)

        for pid, person_data in household_data.groupby('pid'):

            trips = person_data.sort_values('seq')
            home_area = trips.hzone.iloc[0]
            origin_area = trips.ozone.iloc[0]

            if not origin_area == home_area:
                logger.warning(f" Person pid:{pid} plan does not start with 'home' activity")

            if person_attributes is not None:
                person_attribute_dict = person_attributes.loc[pid].to_dict()
            else:
                person_attribute_dict = None

            person = core.Person(
                pid,
                freq=person_data.freq.iloc[0],
                attributes=person_attribute_dict,
                # home_area=home_area
            )

            first_act = trips.iloc[0].activity.lower()
            if not first_act == "home":
                logger.warning(f" Person pid:{pid} hid:{hid} plan does not start with 'home' activity")

            person.add(
                activity.Activity(
                    seq=0,
                    act=first_act,
                    area=origin_area,
                    start_time=utils.minutes_to_datetime(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                person.add(
                    activity.Leg(
                        seq=n,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=utils.minutes_to_datetime(trip.tst),
                        end_time=utils.minutes_to_datetime(trip.tet)
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=trip.activity.lower(),
                        area=trip.dzone,
                        start_time=utils.minutes_to_datetime(trip.tet),
                    )
                )

            person.plan.finalise()
            household.add(person)

        population.add(household)

    return population


def load_travel_diary_from_to(
    trip_diary:pd.DataFrame,
    person_attributes:Union[pd.DataFrame,None]=None,
    hh_attributes:Union[pd.DataFrame,None]=None,
    sample_perc:Union[float,None]=None,
    ):
    """
    Turn Diary Plan tabular data inputs (derived from travel survey and attributes) into core population
    format. This is a variation of the standard load_travel_diary() method because it does not require
    activity inference or home location.
    We expect broadly the same data schema except rather than purp (purpose) we use trips oact (origin activity)
    and dact (destination activity).
    :param trip_diary: DataFrame
    :param person_attributes: DataFrame
    :param hh_attributes: DataFrame
    :param sample_perc: Float. If different to None, it samples the travel population by the corresponding percentage.
    :return: core.Population
    """
    # TODO check for required col headers and give useful error?

    logger = logging.getLogger(__name__)

    if not isinstance(trip_diary, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    if person_attributes is not None and not isinstance(person_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for population person attributes")

    if hh_attributes is not None and not isinstance(hh_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for population household attributes")

    if sample_perc is not None:
        trip_diary = sample_population(
            trip_diary,
            sample_perc,
            weight_col='freq'
            )  # sample the travel population

    population = core.Population()

    for hid, household_data in trip_diary.groupby('hid'):

        if hh_attributes is not None:
            hh_attribute_dict = hh_attributes.loc[hid].to_dict()
        else:
            hh_attribute_dict = None

        household = core.Household(hid, attributes=hh_attribute_dict)

        for pid, person_data in household_data.groupby('pid'):

            if person_attributes is not None:
                person_attribute_dict = person_attributes.loc[pid].to_dict()
            else:
                person_attribute_dict = None

            person = core.Person(
                pid,
                freq=person_data.iloc[0].freq,
                attributes=person_attribute_dict,
            )

            trips = person_data.sort_values('seq')

            first_act = trips.iloc[0].oact.lower()
            if not first_act == "home":
                logger.warning(f" Person pid:{pid} hid:{hid} plan does not start with 'home' activity")

            person.add(
                activity.Activity(
                    seq=0,
                    act=first_act,
                    area=trips.iloc[0].ozone,
                    start_time=utils.minutes_to_datetime(0),
                )
            )

            for n in range(len(trips)):
                trip = trips.iloc[n]

                person.add(
                    activity.Leg(
                        seq=n,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_time=utils.minutes_to_datetime(trip.tst),
                        end_time=utils.minutes_to_datetime(trip.tet)
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=trip.dact.lower(),
                        area=trip.dzone,
                        start_time=utils.minutes_to_datetime(trip.tet),
                    )
                )

            person.plan.finalise()
            household.add(person)

        population.add(household)

    return population


def read_matsim(
        plans_path,
        attributes_path=None,
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
    logger = logging.getLogger(__name__)

    population = core.Population()

    if attributes_path:
        attributes_map = load_attributes_map(attributes_path)

    for person_id, plan in selected_plans(plans_path):

        if attributes_path:
            attributes = attributes_map[person_id]
        else:
            attributes = {}

        person = core.Person(person_id, attributes=attributes, freq=weight)

        act_seq = 0
        leg_seq = 0
        arrival_dt = datetime(1900, 1, 1)
        departure_dt = None

        for stage in plan:
            """
            Loop through stages incrementing time and extracting attributes.
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
                    departure_dt = utils.safe_strptime(
                        stage.get('end_time', '23:59:59')
                    )

                if departure_dt < arrival_dt:
                    logger.warning(f"Negative duration activity found at pid={person_id}")

                person.add(
                    activity.Activity(
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
                network_route = None
                route_id = None
                service_id = None
                o_stop = None
                d_stop = None
                for r in stage:
                    network_route = r.text
                    if network_route is not None:
                        if 'PT' in network_route:
                            pt_details = network_route.split('===')
                            o_stop = pt_details[1]
                            d_stop = pt_details[4]
                            service_id = pt_details[2]
                            route_id = pt_details[3]
                        else:
                            network_route = network_route.split(' ')

                leg_seq += 1

                trav_time = stage.get('trav_time')
                if trav_time:
                    h, m, s = trav_time.split(":")
                    leg_duration = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                    arrival_dt = departure_dt + leg_duration
                else:
                    arrival_dt = departure_dt  # todo this assumes 0 duration unless already known

                person.add(
                    activity.Leg(
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
                        o_stop=o_stop,
                        d_stop=d_stop,
                        service_id=service_id,
                        route_id=route_id,
                        network_route=network_route
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
                household = core.Household(attributes.get(household_key))
                household.add(person)
                population.add(household)
        else:  # not using households, create dummy household
            household = core.Household(person_id)
            household.add(person)
            population.add(household)

    return population


def load_attributes_map(attributes_path):
    """
    Given path to MATSim attributes input, return dictionary of attributes (as dict)
    """
    attributes_map = {}
    people = utils.get_elems(attributes_path, "object")
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
    for person in utils.get_elems(plans_path, "person"):
        for plan in person:
            if plan.get('selected') == 'yes':
                yield person.get('id'), plan


def sample_population(trips_df, sample_perc, attributes_df=None, weight_col='freq'):
    """
    Return the trips of a random sample of the travel population.
    We merge the trips and attribute datasets to enable probability weights based on population demographics.

    :params DataFrame trips_df: Trips dataset
    :params DataFrame attributes_df: Population attributes dataset.
    :params float sample_perc: Sampling percentage
    :params string weight_col: The field to use for probability weighting

    :return: Pandas DataFrame, a sampled version of the trips_df dataframe
    """
    if attributes_df is not None:
        sample_pids = trips_df.groupby('pid')[['freq']].sum().join(
            attributes_df, how='left'
        ).sample(
            frac=sample_perc, weights=weight_col
            ).index
    else:
        sample_pids = trips_df.groupby('pid')[['freq']].sum().sample(
            frac=sample_perc, weights=weight_col
            ).index

    return trips_df[trips_df.pid.isin(sample_pids)]


def load_pickle(path):
    with open(path, 'rb') as file:
        return pickle.load(file)
