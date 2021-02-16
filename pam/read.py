from numpy import DataSource
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
    trips: Union[pd.DataFrame, str],
    persons_attributes: Union[pd.DataFrame, str, None] = None,
    hhs_attributes: Union[pd.DataFrame, str, None] = None,
    sample_perc: Union[float, None] = None,
    tour_based: bool = True,
    from_to: bool = False,
    include_loc: bool = False,
    sort_by_seq: Union[bool, None] = None,
    trip_freq_as_person_freq: bool = False,
    trip_freq_as_hh_freq: bool = False,
    ):
    """
    Turn standard tabular data inputs (travel survey and attributes) into core population format.
    :param trips: DataFrame
    :param persons_attributes: DataFrame
    :param hhs_attributes: DataFrame
    :param sample_perc: Float. If different to None, it samples the travel population by the corresponding percentage
    :param tour_based: bool=True, set to False to force a simpler trip-based purpose parser
    :param from_to: bool=False, set to True to force the from-to purpose parser (requires 'oact' and 'dact' trips columns)
    :param include_loc: bool=False, optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' trips columns)
    :param sort_by_seq=None, optionally force trip sorting as True or False
    :param trip_freq_as_person_freq:bool=False.
    :param trip_freq_as_hh_freq:bool=False.
    :return: core.Population
    """
    # TODO check for required col headers and give useful error?

    logger = logging.getLogger(__name__)

    if isinstance(trips, str):
        logger.warning(f"Attempting to load trips dataframe from path: {trips}")
        trips = pd.read_csv(trips)

    if isinstance(persons_attributes, str):
        logger.warning(f"Attempting to load trips dataframe from path: {persons_attributes}")
        persons_attributes = pd.read_csv(persons_attributes)

    if isinstance(hhs_attributes, str):
        logger.warning(f"Attempting to load trips dataframe from path: {hhs_attributes}")
        hhs_attributes = pd.read_csv(hhs_attributes)

    if not isinstance(trips, pd.DataFrame):
        raise UserWarning("Unrecognised input for population travel diaries")

    if persons_attributes is not None and not isinstance(persons_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for person_attributes")

    if hhs_attributes is not None and not isinstance(hhs_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for hh_attributes")

    if ('oact' in trips.columns and 'dact' in trips.columns) or from_to:
        logger.warning("Using from-to activity parser using 'oact' and 'dact' columns")
        from_to = True

        # check that trips diary has required fields
        missing = {'pid', 'ozone', 'dzone', 'oact', 'dact', 'mode', 'tst', 'tet'} - set(trips.columns)
        if missing:
            raise UserWarning(f"Input trips_diary missing required column names: {missing}.")

    else:
        if tour_based:
            logger.warning("Using tour based purpose parser using (recommended)")
        else:
            logger.warning(
                """
                Using simple trip based purpose parser using, this assumes first activity is 'home'.
                If you do not wish to assume this, try setting 'tour_based' = True (default).
                """
                )
        
        # check that trips diary has required fields
        missing = {'pid', 'ozone', 'dzone', 'purp', 'mode', 'tst', 'tet'} - set(trips.columns)
        if missing:
            raise UserWarning(f"Input trips_diary missing required column names: {missing}.")

    if sort_by_seq and 'seq' not in trips.columns:
        raise UserWarning(
    f"""
    You must include a trips 'seq' column if you wish to sort trips:
    Either include a 'seq' column or use the existing ordering by 
    setting 'sort_by_seq' = False/None (default).
    """
    )

    if include_loc and not all(x in trips.columns for x in ['start_loc', 'end_loc']):
        raise UserWarning(
    f"""
    You must include a trips 'start_loc' and 'end_loc' column if you wish to use precise locations:
    Either include a 'start_loc' and 'end_loc' column or set 'include_loc' = False (default).
    Note that these columns must be shapely Point geometries.
    """
    )

    # check that person_attributes has required fields if used
    if persons_attributes is not None and 'pid' not in persons_attributes.columns:
        raise UserWarning(f"Input person_attributes dataframe missing required unique identifier column: 'pid'.")

    # check if hh_attributes are being used
    if hhs_attributes is not None:
        if 'hid' not in hhs_attributes.columns:
            raise UserWarning(f"Input hh_attributes dataframe missing required unique identifier column: 'hid'.")

        if 'hid' in trips.columns:
            logger.info("Using person to household mapping from trips_diary data")
        elif 'hid' in persons_attributes.columns:
            logger.info("Loading person to household mapping from person_attributes data")
            person_hh_mapping = dict(zip(persons_attributes.pid, persons_attributes.hid))
            trips['hid'] = trips.pid.map(person_hh_mapping)
        else:
            raise UserWarning(
        f"""
        Household attributes found but failed to build person to household mapping from provided inputs:
        Please provide a household ID field ('hid') in either the trips_dairy or person_attributes inputs.
        """
        )

    # add hid to trips if not already added
    if not 'hid' in trips.columns:
        logger.warning(
            """
            No household entities found, households will be composed of individual persons using 'pid':
            If you wish to correct this, please add 'hid' to either the trips or persons_attributes inputs.
            """
            )
        trips['hid'] = trips.pid

    # add hzone to trips_diary
    if not 'hzone' in trips.columns:
        if hhs_attributes is not None and 'hzone' in hhs_attributes.columns:
            logger.info("Loading household area ('hzone') from hh_attributes input.")
            hh_mapping = dict(zip(hhs_attributes.hid, hhs_attributes.hzone))
            trips['hzone'] = trips.hid.map(hh_mapping)
        elif persons_attributes is not None and 'hzone' in persons_attributes.columns and 'hid' in persons_attributes.columns:
            logger.info("Loading household area ('hzone') from person_attributes input.")
            hh_mapping = dict(zip(persons_attributes.hid, persons_attributes.hzone))
            trips['hzone'] = trips.hid.map(hh_mapping)
        else:
            logger.warning(
        f"""
        Unable to load household area ('hzone') - not found in trips_diary or unable to build from attributes.
        Pam will try to infer home location from activities, but thos behaviour is not recommended.
        """
        )

    if  trip_freq_as_person_freq:  # use trip freq as person freq
        if 'freq' not in trips.columns:
            raise UserWarning(
                f"""
                You have opted to use 'trip_freq_as_person_freq' but cannot build this mapping:
                Please check 'freq' is included in the trips_diary input.
                """
                )
            
        logger.info("Loading person freq ('freq') from trips_diary freq input.")
        pid_freq_map = dict(zip(trips.pid, trips.freq))  # this will take last freq from trips

        if persons_attributes is None:
            logger.info("Building new person attributes dataframe to hold person frequency.")
            persons_attributes = pd.DataFrame({'pid': list(pid_freq_map.keys()), 'freq': list(pid_freq_map.values())})
        else:
            logger.info("Adding freq to person attributes using trip frequency.")
            persons_attributes['freq'] = persons_attributes.pid.map(pid_freq_map)

        trips.drop('freq', axis=1, inplace=True)

    if  trip_freq_as_hh_freq:
        if 'freq' not in trips.columns:
            raise UserWarning(
                f"""
                You have opted to use 'trip_freq_as_hh_freq' but cannot build this mapping:
                Please check 'freq' is included in the trips_diary input.
                """
                )
        if 'hid' not in trips.columns:
            raise UserWarning(
                f"""
                You have opted to use 'trip_freq_as_hh_freq' but cannot build this mapping:
                Please check 'hid' is included in the trips_diary input.
                """
                )
            
        logger.info("Loading houshold freq ('freq') from trips_diary freq input.")
        hid_freq_map = dict(zip(trips.hid, trips.freq))  # this will take last freq from trips

        if hhs_attributes is None:
            logger.info("Building new household attributes dataframe to hold houshold frequency.")
            hhs_attributes = pd.DataFrame({'hid': list(hid_freq_map.keys()), 'freq': list(hid_freq_map.values())})
        else:
            logger.info("Adding freq to household attributes using trip frequency.")
            hhs_attributes['freq'] = hhs_attributes.pid.map(hid_freq_map)

        trips.drop('freq', axis=1, inplace=True)

    # Add an empty frequency fields if required
    if 'freq' not in trips.columns:
        logger.warning("Using freq of 'None' for all trips.")
        trips['freq'] = None

    if persons_attributes is not None and 'freq' not in persons_attributes.columns:
        logger.warning("Using freq of 'None' for all persons.")
        persons_attributes['freq'] = None

    if hhs_attributes is not None and 'freq' not in hhs_attributes.columns:
        logger.warning("Using freq of 'None' for all households.")
        hhs_attributes['freq'] = None

    if sample_perc is not None:
        if 'freq' not in trips.columns:
            raise UserWarning(
                f"""
                You have opted to use a sample ({sample_perc}, but this option requires that trips frequencies are set:):
                Please add a 'freq' column to the trips dataframe or remove sampling (set 'sample_perc' = None).
                """
                )
        trips = sample_population(
            trips=trips,
            sample_perc=sample_perc,
            weight_col='freq'
            )  # sample the travel population

    if from_to:
        logger.debug("Initiating from-to parser.")
        return from_to_travel_diary_read(
            trips = trips,
            persons_attributes = persons_attributes,
            hhs_attributes = hhs_attributes,
            include_loc = include_loc,
            sort_by_seq  = sort_by_seq,
        )

    if tour_based:
        logger.debug("Initiating tour-based parser.")
        return tour_based_travel_diary_read(
            trips = trips,
            persons_attributes = persons_attributes,
            hhs_attributes = hhs_attributes,
            include_loc = include_loc,
            sort_by_seq  = sort_by_seq,
            )

    logger.debug("Initiating trip-based parser.")
    return trip_based_travel_diary_read(
        trips = trips,
        persons_attributes = persons_attributes,
        hhs_attributes = hhs_attributes,
        include_loc = include_loc,
        sort_by_seq = sort_by_seq,
        )


def tour_based_travel_diary_read(
    trips: pd.DataFrame,
    persons_attributes: Union[pd.DataFrame, None] = None,
    hhs_attributes: Union[pd.DataFrame, None] = None,
    include_loc = False,
    sort_by_seq: Union[bool, None] = None,
    ):
    """
    Complex travel diray reader. Will try to infer home activiity and tour based purposes.
    :param trips: DataFrame
    :param persons_attributes: DataFrame
    :param hhs_attributes: DataFrame
    :param include_loc=False, bool, optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns)
    :param sort_by_seq=None, optionally force trip sorting as True or False
    :return: core.Population
    """

    population = core.Population()

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    for hid, household_trips in trips.groupby('hid'):

        if hhs_attributes is not None:
            hh_attributes = hhs_attributes.loc[hid].to_dict()
        else:
            hh_attributes = {}

        household = core.Household(hid, attributes=hh_attributes, freq=hh_attributes.pop('freq', None))

        for pid, person_trips in household_trips.groupby('pid'):
            
            if sort_by_seq:
                person_trips = person_trips.sort_values('seq')

            if persons_attributes is not None:
                person_attributes = persons_attributes.loc[pid].to_dict()
            else:
                person_attributes = {}

            home_area=person_trips.hzone.iloc[0]

            person = core.Person(
                pid,
                attributes=person_attributes,
                home_area=home_area,
                freq=person_attributes.pop('freq', None)
                )

            loc = None
            if include_loc:
                loc = person_trips.start_loc.iloc[0]

            person.add(
                activity.Activity(
                    seq=0,
                    act=None,
                    area=person_trips.ozone.iloc[0],
                    loc=loc,
                    start_time=utils.parse_time(0),
                )
            )

            for n in range(len(person_trips)):
                trip = person_trips.iloc[n]

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
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        freq=trip.freq,
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=None,
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.parse_time(trip.tet),
                    )
                )

            person.plan.finalise()
            person.plan.infer_activities_from_tour_purpose()

            household.add(person)

        population.add(household)

    return population


def trip_based_travel_diary_read(
    trips: pd.DataFrame,
    persons_attributes: Union[pd.DataFrame, None] = None,
    hhs_attributes: Union[pd.DataFrame, None] = None,
    include_loc = False,
    sort_by_seq: Union[bool, None] = None,
    ):
    """
    Turn Activity Plan tabular data inputs (derived from travel survey and attributes) into core population
    format. This is a variation of the standard load_travel_diary() method because it does not require
    activity inference. However all plans are expected to be tour based, so assumed to start and end at home.
    We expect broadly the same data schema except rather than trip 'purpose' we use trips 'activity'.
    :param trips: DataFrame
    :param persons_attributes: DataFrame
    :param hhs_attributes: DataFrame
    :param include_loc=False, bool, optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns)
    :param sort_by_seq=None, optionally force trip sorting as True or False
    :return: core.Population
    """

    logger = logging.getLogger(__name__)

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    population = core.Population()

    for hid, household_trips in trips.groupby('hid'):

        if hhs_attributes is not None:
            hh_attributes = hhs_attributes.loc[hid].to_dict()
        else:
            hh_attributes = {}

        household = core.Household(hid, attributes=hh_attributes, freq=hh_attributes.pop('freq', None))

        for pid, person_trips in household_trips.groupby('pid'):

            if sort_by_seq:
                person_trips = person_trips.sort_values('seq')

            home_area = person_trips.hzone.iloc[0]
            origin_area = person_trips.ozone.iloc[0]

            if not origin_area == home_area:
                logger.warning(f" Person pid:{pid} plan does not start with 'home' activity")

            if persons_attributes is not None:
                person_attributes = persons_attributes.loc[pid].to_dict()
            else:
                person_attributes = {}

            person = core.Person(
                pid,
                attributes=person_attributes,
                freq=person_attributes.pop('freq', None),
                # home_area=home_area
            )

            loc = None
            if include_loc:
                loc = person_trips.start_loc.iloc[0]

            person.add(
                activity.Activity(
                    seq=0,
                    act='home',
                    area=origin_area,
                    loc=loc,
                    start_time=utils.parse_time(0),
                )
            )

            for n in range(len(person_trips)):
                trip = person_trips.iloc[n]

                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc

                person.add(
                    activity.Leg(
                        seq=n,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet)
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=trip.activity.lower(),
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.parse_time(trip.tet),
                    )
                )

            person.plan.finalise()
            household.add(person)

        population.add(household)

    return population


def from_to_travel_diary_read(
    trips: pd.DataFrame,
    persons_attributes: Union[pd.DataFrame, None] = None,
    hhs_attributes: Union[pd.DataFrame, None] = None,
    include_loc = False,
    sort_by_seq: Union[bool, None] = False,
    ):
    """
    Turn Diary Plan tabular data inputs (derived from travel survey and attributes) into core population
    format. This is a variation of the standard load_travel_diary() method because it does not require
    activity inference or home location.
    We expect broadly the same data schema except rather than purp (purpose) we use trips oact (origin activity)
    and dact (destination activity).
    :param trips: DataFrame
    :param persons_attributes: DataFrame
    :param hhs_attributes: DataFrame
    :return: core.Population
    :param include_loc=False, bool, optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns)
    :param sort_by_seq=None, optionally force trip sorting as True or False
    """
    # TODO check for required col headers and give useful error?

    logger = logging.getLogger(__name__)

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    population = core.Population()

    for hid, household_trips in trips.groupby('hid'):

        if hhs_attributes is not None:
            hh_attributes = hhs_attributes.loc[hid].to_dict()
        else:
            hh_attributes = {}

        household = core.Household(hid, attributes=hh_attributes, freq=hh_attributes.pop('freq', None))

        for pid, person_trips in household_trips.groupby('pid'):

            if sort_by_seq:
                person_trips = person_trips.sort_values('seq')

            if persons_attributes is not None:
                person_attributes = persons_attributes.loc[pid].to_dict()
            else:
                person_attributes = {}

            person = core.Person(
                pid,
                attributes=person_attributes,
                freq=person_attributes.pop('freq', None),
            )

            first_act = person_trips.iloc[0].oact.lower()
            if not first_act == "home":
                logger.warning(f" Person pid:{pid} hid:{hid} plan does not start with 'home' activity")

            loc = None
            if include_loc:
                loc = person_trips.start_loc.iloc[0]

            person.add(
                activity.Activity(
                    seq=0,
                    act=first_act,
                    area=person_trips.iloc[0].ozone,
                    loc=loc,
                    start_time=utils.parse_time(0),
                )
            )

            for n in range(len(person_trips)):
                trip = person_trips.iloc[n]

                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc

                person.add(
                    activity.Leg(
                        seq=n,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet)
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=trip.dact.lower(),
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.parse_time(trip.tet),
                    )
                )

            person.plan.finalise()
            household.add(person)

        population.add(household)

    return population


def read_matsim(
        plans_path,
        attributes_path=None,
        weight=100,
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
                household = core.Household(attributes.get(household_key), freq=weight)
                household.add(person)
                population.add(household)
        else:  # not using households, create dummy household
            household = core.Household(person_id, freq=weight)
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
