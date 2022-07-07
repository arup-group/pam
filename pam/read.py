import pandas as pd
from shapely.geometry import Point
from datetime import datetime, timedelta
import logging
import pickle
from typing import Union, Optional
import json

import pam.core as core
import pam.activity as activity
import pam.utils as utils
from pam.vehicle import VehicleType, Vehicle, ElectricVehicle


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
        raise UserWarning("Unrecognised input for trips input.")

    if persons_attributes is not None and not isinstance(persons_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for person_attributes")

    if hhs_attributes is not None and not isinstance(hhs_attributes, pd.DataFrame):
        raise UserWarning("Unrecognised input for hh_attributes")

    # reset indexes if named
    for table in [trips, persons_attributes, hhs_attributes]:
        if table is not None and table.index.name is not None:
            table.reset_index(inplace=True)

    if ('oact' in trips.columns and 'dact' in trips.columns) or from_to:
        logger.warning("Using from-to activity parser using 'oact' and 'dact' columns")
        from_to = True

        # check that trips diary has required fields
        missing = {'pid', 'ozone', 'dzone', 'oact', 'dact', 'mode', 'tst', 'tet'} - set(trips.columns)
        if missing:
            raise UserWarning(f"Input trips_diary missing required column names: {missing}.")

    else:
        if tour_based:
            logger.warning("Using tour based purpose parser (recommended)")
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

    if trip_freq_as_person_freq:  # use trip freq as person freq
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

    if trip_freq_as_hh_freq:
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
            hhs_attributes['freq'] = hhs_attributes.hid.map(hid_freq_map)

        trips.drop('freq', axis=1, inplace=True)

    # add hid to trips if not already added
    if not 'hid' in trips.columns \
        and (persons_attributes is None or 'hid' not in persons_attributes.columns) \
        and (hhs_attributes is None or 'pid' not in hhs_attributes.columns):
        logger.warning(
            """
            No household entities found, households will be composed of individual persons using 'pid':
            If you wish to correct this, please add 'hid' to either the trips or persons_attributes inputs.
            """
            )
        trips['hid'] = trips.pid


    # check that person_attributes has required fields if used
    if persons_attributes is not None:
        if 'pid' not in persons_attributes.columns and not persons_attributes.index.name == 'pid':
            raise UserWarning(f"Input person_attributes dataframe missing required unique identifier column: 'pid'.")

        if 'hid' not in persons_attributes and 'hid' in trips:
            logger.warning("Adding pid->hh mapping to persons_attributes from trips.")
            mapping = dict(zip(trips.pid, trips.hid))
            persons_attributes['hid'] = persons_attributes.pid.map(mapping)

        if 'hzone' not in persons_attributes.columns and 'hid' in persons_attributes.columns:
            if hhs_attributes is not None and 'hzone' in hhs_attributes:
                logger.warning("Adding home locations to persons attributes using hhs_attributes.")
                mapping = dict(zip(hhs_attributes.hid, hhs_attributes.hzone))
                persons_attributes['hzone'] = persons_attributes.hid.map(mapping)
            elif 'hzone' in trips and 'hid' in trips:
                logger.warning("Adding home locations to persons attributes using trips attributes.")
                mapping = dict(zip(trips.hid, trips.hzone))
                persons_attributes['hzone'] = persons_attributes.hid.map(mapping)


    # check if hh_attributes are being used
    if hhs_attributes is not None:
        if 'hid' not in hhs_attributes.columns and not hhs_attributes.index.name == 'hid':
            raise UserWarning(f"Input hh_attributes dataframe missing required unique identifier column: 'hid'.")

        if 'hid' in trips.columns:
            logger.info("Using person to household mapping from trips_diary data")
            if persons_attributes is not None and 'hid' not in persons_attributes.columns:
                logger.info("Loading person to household mapping for person_attributes from trips data")
                person_hh_mapping = dict(zip(trips.pid, trips.hid))
                persons_attributes['hid'] = persons_attributes.pid.map(person_hh_mapping)

        elif persons_attributes is not None and 'hid' in persons_attributes.columns:
            logger.info("Loading person to household mapping from person_attributes data")
            person_hh_mapping = dict(zip(persons_attributes.pid, persons_attributes.hid))
            trips['hid'] = trips.pid.map(person_hh_mapping)

        else:
            raise UserWarning(
            f"""
            Household attributes found but failed to build person to household mapping from provided inputs:
            Please provide a household ID field ('hid') in either the trips_diary or person_attributes inputs.
            """
            )

        if 'hzone' not in hhs_attributes.columns:
            if persons_attributes is not None and 'hzone' in persons_attributes and 'hid' in persons_attributes.columns:
                logger.warning("Adding home locations to hhs attributes using persons_attributes.")
                mapping = dict(zip(persons_attributes.hid, persons_attributes.hzone))
                hhs_attributes['hzone'] = hhs_attributes.hid.map(mapping)
            elif 'hzone' in trips and 'hid' in trips:
                logger.warning("Adding home locations to hhs attributes using trips attributes.")
                mapping = dict(zip(trips.hid, trips.hzone))
                hhs_attributes['hzone'] = hhs_attributes.hid.map(mapping)

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
        Pam will try to infer home location from activities, but this behaviour is not recommended.
        """
        )

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

    logger.debug("Resetting trips index if required")
    if trips.index.name is not None:
        persons_attributes.reset_index(inplace=True)

    if persons_attributes is not None:
        logger.debug("Setting persons_attributes index to pid")
        if persons_attributes.index.name is None:
            persons_attributes.set_index('pid', inplace=True)
        elif not persons_attributes.index.name == 'pid':
            persons_attributes = persons_attributes.reset_index().set_index('pid')

    if hhs_attributes is not None:
        logger.debug("Setting households_attributes index to hid")
        if hhs_attributes.index.name is None:
            hhs_attributes.set_index('hid', inplace=True)
        elif not hhs_attributes.index.name == 'hid':
            hhs_attributes = hhs_attributes.reset_index().set_index('hid')

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


def build_population(
    trips: Optional[pd.DataFrame] = None,
    persons_attributes: Optional[pd.DataFrame] = None,
    hhs_attributes: Optional[pd.DataFrame] = None
    ):
    """
    Build a population of households and persons (without plans)
    from available trips, persons_attributes and households_attributes
    data.
    Details of required table formats are in the README.

    Args:
        trips (Optional[pd.DataFrame]): trips table
        persons_attributes (Optional[pd.DataFrame]): persons attributes table
        hhs_attributes (Optional[pd.DataFrame]): households attributes table

    Returns:
        pam.Population: population object
    """
    population = core.Population()
    add_hhs_from_hhs_attributes(population=population, hhs_attributes=hhs_attributes)
    add_hhs_from_persons_attributes(population=population, persons_attributes=persons_attributes)
    add_hhs_from_trips(population=population, trips=trips)
    add_persons_from_persons_attributes(population=population, persons_attributes=persons_attributes)
    add_persons_from_trips(population=population, trips=trips)

    return population


def add_hhs_from_hhs_attributes(
    population: core.Population,
    hhs_attributes: Optional[pd.DataFrame] = None
    ):
    logger = logging.getLogger(__name__)

    if hhs_attributes is None:
        return None

    logger.info("Adding hhs from hhs_attributes")
    for hid, hh in hhs_attributes.groupby('hid'):
        if hid not in population.households:
            hh_attributes = hhs_attributes.loc[hid].to_dict()
            household = core.Household(
                hid,
                attributes=hh_attributes,
                freq=hh_attributes.pop("freq", None),
                area=hh_attributes.pop("hzone", None)
                )
            population.add(household)


def add_hhs_from_persons_attributes(
    population: core.Population,
    persons_attributes: Optional[pd.DataFrame] = None
    ):
    logger = logging.getLogger(__name__)

    if persons_attributes is None or 'hid' not in persons_attributes.columns:
        return None

    if 'hzone' in persons_attributes.columns:
        hzone_lookup = persons_attributes.groupby('hid').head(1).set_index('hid').hzone.to_dict()
    else:
        hzone_lookup = {}

    logger.info("Adding hhs from persons_attributes")
    for hid, hh_data in persons_attributes.groupby('hid'):
        if hid not in population.households:
            hzone = hzone_lookup.get(hid)
            household = core.Household(
                hid,
                area=hzone
                )
            population.add(household)


def add_hhs_from_trips(
    population: core.Population,
    trips: Optional[pd.DataFrame] = None,
    ):
    logger = logging.getLogger(__name__)

    if trips is None or 'hid' not in trips.columns:
        return None

    logger.info("Adding hhs from trips")
    for hid, hh_data in trips.groupby('hid'):
        if hid not in population.households:
            hzone = hh_data.iloc[0].to_dict().get("hzone")
            household = core.Household(
                hid,
                area=hzone
                )
            population.add(household)


def add_persons_from_persons_attributes(
    population: core.Population,
    persons_attributes: Optional[pd.DataFrame] = None,
    ):
    logger = logging.getLogger(__name__)

    if persons_attributes is None or 'hid' not in persons_attributes.columns:
        return None

    persons_attributes_dict  = persons_attributes.reset_index().set_index(['hid','pid']).to_dict('index')

    logger.info("Adding persons from persons_attributes")
    for hid, hh_data in persons_attributes.groupby('hid'):
        household = population.get(hid)
        if household is None:
            logger.warning(f"Failed to find household {hid} in population - unable to add person.")
            continue
        for pid in hh_data.index:
            if pid in household.people:
                continue

            person_attributes = persons_attributes_dict[hid, pid]

            person = core.Person(
                pid,
                attributes=person_attributes,
                home_area=person_attributes.get('hzone', None),
                freq=person_attributes.pop('freq', None)
                )
            household.add(person)


def add_persons_from_trips(
    population: core.Population,
    trips: Optional[pd.DataFrame] = None,
    ):
    logger = logging.getLogger(__name__)

    if trips is None or 'hid' not in trips.columns:
        return None

    logger.info("Adding persons from trips")
    for (hid, pid), hh_person_data in trips.groupby(['hid', 'pid']):
        household = population.households.get(hid)
        if household is None:
            logger.warning(f"Failed to find household {hid} in population - unable to add person.")
            continue
        if pid in household.people:
            continue
        person = core.Person(
            pid,
            home_area=hh_person_data.iloc[0].to_dict().get("hzone"),
            )
        household.add(person)

def hh_person_df_to_dict(
    df: pd.DataFrame,
    key_hh: str,
    key_person: str,
    ):
    """
    Restructure a dataframe as a nested dictionary of dataframes,
        where the first level is the household index,
        the second level is the person index,
        the value is the dataframe slice corresponding to that person

    The dictionary structure allows for much faster access to a person's data.
    :params pd.DataFrame df: the pandas dataframe to reindex
    :params str key_hh: the household key column name
    :params str key_person: the person key column name
    :params boolean values_dict: whether to convert the person data to a dictionary as well
    """
    df_dict = {x:{} for x in df[key_hh].unique()}
    for (hid, pid), person_data in df.groupby([key_hh,key_person]):
        df_dict[hid][pid] = person_data
    return df_dict

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

    population = build_population(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    if sort_by_seq:
        trips = trips.sort_values(['hid','pid','seq'])

    trips_dict = hh_person_df_to_dict(trips, 'hid', 'pid') # convert to dict for faster indexing

    for hid, household in population:
        for pid, person in household:
            person_trips = trips_dict.get(hid, {}).get(pid, pd.DataFrame())

            if not len(person_trips):
                person.stay_at_home()
                continue

            loc = None
            if include_loc:
                loc = person_trips.start_loc.iloc[0]

            person = population[hid][pid]

            person.add(
                activity.Activity(
                    seq=0,
                    act=None,
                    area=person_trips.ozone.iloc[0],
                    loc=loc,
                    start_time=utils.parse_time(0),
                )
            )

            for n, trip in person_trips.iterrows():

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
                        distance = trip.get('distance'),
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

            person.plan.finalise_activity_end_times()
            person.plan.infer_activities_from_tour_purpose()
            person.plan.set_leg_purposes()

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

    population = build_population(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    if sort_by_seq:
        trips = trips.sort_values(['hid','pid','seq'])

    trips_dict = hh_person_df_to_dict(trips, 'hid', 'pid') # convert to dict for faster indexing

    for hid, household in population:
        for pid, person in household:
            person_trips = trips_dict.get(hid, {}).get(pid, pd.DataFrame())

            if not len(person_trips):
                person.stay_at_home()
                continue

            home_area = household.location.area or person_trips.hzone.iloc[0]
            origin_area = person_trips.ozone.iloc[0]

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

            for n, trip in person_trips.iterrows():

                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc
                purpose = trip.purp.lower()

                person.add(
                    activity.Leg(
                        seq=n,
                        purp=purpose,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        distance = trip.get('distance')
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=purpose,
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.parse_time(trip.tet),
                    )
                )

            person.plan.finalise_activity_end_times()
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
    logger = logging.getLogger(__name__)

    population = build_population(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and 'seq' in trips.columns:
        sort_by_seq = True

    if sort_by_seq:
        trips = trips.sort_values(['hid','pid','seq'])

    trips_dict = hh_person_df_to_dict(trips, 'hid', 'pid') # convert to dict for faster indexing

    for hid, household in population:
        for pid, person in household:
            person_trips = trips_dict.get(hid, {}).get(pid, pd.DataFrame())

            if not len(person_trips):
                person.stay_at_home()
                continue

            first_act = person_trips.iloc[0].oact.lower()
            if not first_act == "home":
                logger.warning(f" Person pid:{pid} hid:{hid} plan does not start with 'home' activity: {first_act}")

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

            for n, trip in person_trips.iterrows():

                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc
                purpose=trip.dact.lower()

                person.add(
                    activity.Leg(
                        seq=n,
                        purp=purpose,
                        mode=trip['mode'].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        distance = trip.get('distance')
                    )
                )

                person.add(
                    activity.Activity(
                        seq=n + 1,
                        act=purpose,
                        area=trip.dzone,
                        loc=end_loc,
                        start_time=utils.parse_time(trip.tet),
                    )
                )

            person.plan.finalise_activity_end_times()
            household.add(person)

        population.add(household)

    return population


def read_matsim(
        plans_path,
        attributes_path = None,
        all_vehicles_path = None,
        electric_vehicles_path = None,
        weight : int = 100,
        version : int = 12,
        household_key : Union[str, None] = None,
        simplify_pt_trips : bool = False,
        autocomplete : bool = True,
        crop : bool = True,
        keep_non_selected : bool = False
):
    """
    Load a MATSim format population into core population format.
    It is possible to maintain the unity of housholds using a household uid in
    the attributes input, ie:
    <attribute class="java.lang.String" name="hid">hh_0001</attribute>
    :param plans: path to matsim format xml
    :param attributes: path to matsim format xml
    :param all_vehicles_path: path to matsim all_vehicles xml file
    :param electric_vehicles_path: path to matsim electric_vehicles xml
    :param weight: int
    :param version: int {11,12}, default = 12
    :param household_key: {str, None}
    :param keep_non_selected: Whether to parse non-selected plans (storing them in person.plans_non_selected).
    :return: Population
    """
    logger = logging.getLogger(__name__)

    population = core.Population()

    if attributes_path is not None and version == 12:
        raise UserWarning(
    """
    You have provided an attributes_path and enables matsim version 12, but
    v12 does not require an attributes input:
    Either remove the attributes_path arg, or enable version 11.
    """
    )

    if version not in [11, 12]:
        raise UserWarning("Version must be set to 11 or 12.")

    vehicles = {}
    if all_vehicles_path:
        vehicles = read_vehicles(all_vehicles_path, electric_vehicles_path)

    attributes_map = {}
    if version == 12:
        attributes_map = load_attributes_map_from_v12(plans_path)
    elif attributes_path:
        attributes_map = load_attributes_map(attributes_path)

    for person_xml in utils.get_elems(plans_path, "person"):
        person_id = person_xml.get('id')
        attributes = attributes_map.get(person_id, {})
        if person_id in vehicles:
            vehicle = vehicles[person_id]
        else:
            vehicle = None
        person = core.Person(person_id, attributes=attributes, freq=weight, vehicle=vehicle)

        for plan_xml in person_xml:
            if plan_xml.get('selected') == 'yes':
                person.plan = parse_matsim_plan(
                    plan_xml=plan_xml, person_id=person_id, version=version, simplify_pt_trips=simplify_pt_trips,
                    crop=crop, autocomplete=autocomplete
                    )
            elif keep_non_selected and plan_xml.get('selected') == 'no':
                person.plans_non_selected.append(
                    parse_matsim_plan(
                        plan_xml=plan_xml, person_id=person_id, version=version, simplify_pt_trips=simplify_pt_trips,
                        crop=crop, autocomplete=autocomplete
                        )
                    )

        # Check if using households, then update population accordingly.
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

def parse_matsim_plan(plan_xml, person_id : str, version : int, simplify_pt_trips : bool, crop : bool, autocomplete : bool) -> activity.Plan:
    """
    Parse a MATSim plan.
    """
    logger = logging.getLogger(__name__)
    act_seq = 0
    leg_seq = 0
    arrival_dt = datetime(1900, 1, 1)
    departure_dt = None
    plan = activity.Plan()

    for stage in plan_xml:
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
                logger.debug(f"Negative duration activity found at pid={person_id}")

            plan.add(
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

            route, mode, network_route, transit_route = \
                extract_route_attributes(stage, version)
            leg_seq += 1
            trav_time = stage.get('trav_time')
            if trav_time:
                h, m, s = trav_time.split(":")
                leg_duration = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                arrival_dt = departure_dt + leg_duration
            else:
                arrival_dt = departure_dt  # todo this assumes 0 duration unless already known

            distance = route.get("distance")
            if distance is not None:
                distance = float(distance)

            boarding_time = transit_route.get("boardingTime")
            if boarding_time is not None:
                boarding_time = utils.matsim_time_to_datetime(boarding_time)

            plan.add(
                activity.Leg(
                    seq=leg_seq,
                    mode=mode,
                    start_link=route.get('start_link'),
                    end_link=route.get('end_link'),
                    start_time=departure_dt,
                    end_time=arrival_dt,
                    distance=distance,
                    service_id = transit_route.get("transitLineId"),
                    route_id = transit_route.get("transitRouteId"),
                    o_stop = transit_route.get("accessFacilityId"),
                    d_stop = transit_route.get("egressFacilityId"),
                    boarding_time = boarding_time,
                    network_route=network_route,
                )
            )

    if simplify_pt_trips:
        plan.simplify_pt_trips()

    plan.set_leg_purposes()

    score = plan_xml.get('score', None)
    if score:
        score = float(score)
    plan.score = score # experienced plan scores

    if crop:
        plan.crop()

    if autocomplete:
        plan.autocomplete_matsim()

    return plan

def extract_route_attributes(leg, version):
    if version == 12:
        return extract_route_v12(leg)
    return extract_route_v11(leg)


def extract_route_v11(leg):
    """
    Extract mode, network route and transit route as available.

    Args:
        leg (xml_leg_element)

    Returns:
        (xml_elem, string, list, dict): (route, mode, network route, transit route)
    """
    route = leg.xpath("route")
    mode = leg.get("mode")
    if not route:
        return {}, mode, None, {}
    route = route[0]
    if mode == "pt":
        return route, mode, None, v11_transit_route(route)
    network_route = route.text
    if network_route is not None:
        return route, mode, network_route.split(" "), {}
    return route, mode, None, {}


def extract_route_v12(leg):
    """
    Extract route_element, mode, network route and transit route as available.

    Args:
        leg (xml_leg_element)

    Returns:
        (xml_element, string, list, dict): (route, mode, network route, transit route)
    """
    route = leg.xpath("route")
    mode = leg.get("mode")
    if not route:
        return {}, mode, None, {}
    route = route[0]
    if route.get("type") == "default_pt":
        return route, mode, None, v12_transit_route(route)
    network_route = route.text
    if network_route is not None:
        return route, mode, network_route.split(" "), {}
    return route, mode, None, {}


def v12_transit_route(route):
    return json.loads(route.text.strip())

def v11_transit_route(route):
    pt_details = route.text.split('===')
    return {
        "accessFacilityId": pt_details[1],
        "transitLineId": pt_details[2],
        "transitRouteId": pt_details[3],
        "egressFacilityId": pt_details[4]
    }


def load_attributes_map_from_v12(plans_path):
    return dict(
        [
            get_attributes_from_plans(elem)
            for elem in utils.get_elems(plans_path, "person")
        ]
    )


def get_attributes_from_plans(elem):
    ident = elem.xpath("@id")[0]
    attributes = {}
    for attr in elem.xpath('./attributes/attribute'):
        attributes[attr.get('name')] = attr.text
    return ident, attributes


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


def read_vehicles(all_vehicles_path, electric_vehicles_path=None):
    """
    Reads all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd and
    electric_vehicles file following format https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd
    :param all_vehicles_path: path to matsim all_vehicles xml file
    :param electric_vehicles_path: path to matsim electric_vehicles xml (optional)
    :return: dictionary of all vehicles: {ID: pam.vehicle.Vehicle or pam.vehicle.ElectricVehicle class object}
    """
    vehicles = read_all_vehicles_file(all_vehicles_path)
    if electric_vehicles_path:
        vehicles = read_electric_vehicles_file(electric_vehicles_path, vehicles)
    return vehicles


def read_all_vehicles_file(path):
    """
    Reads all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
    :param path: path to matsim all_vehicles xml file
    :return: dictionary of all vehicles: {ID: pam.vehicle.Vehicle class object}
    """
    vehicles = {}
    vehicle_types = {}

    for vehicle_type_elem in utils.get_elems(path, "vehicleType"):
        vehicle_types[vehicle_type_elem.get('id')] = VehicleType.from_xml_elem(vehicle_type_elem)

    for vehicle_elem in utils.get_elems(path, "vehicle"):
        vehicles[vehicle_elem.get('id')] = Vehicle(id=vehicle_elem.get('id'),
                                                   vehicle_type=vehicle_types[vehicle_elem.get('type')])

    return vehicles


def read_electric_vehicles_file(path, vehicles: dict = None):
    """
    Reads electric_vehicles file following format https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd
    :param path: path to matsim electric_vehicles xml
    :param vehicles: dictionary of {ID: pam.vehicle.Vehicle} objects, some of which may need to be updated to ElectricVehicle
        based on contents of the electric_vehicles xml file. Optional, if not passed, vehicles will default to the
        VehicleType defaults.
    :return: dictionary of all vehicles: {ID: pam.vehicle.Vehicle or pam.vehicle.ElectricVehicle class object}
    """
    if vehicles is None:
        logging.warning('All Vehicles dictionary was not passed. This will result in defaults for Vehicle Types'
                        'Definitions assumed by the Electric Vehicles')
        vehicles = {}
    for vehicle_elem in utils.get_elems(path, "vehicle"):
        attribs = dict(vehicle_elem.attrib)
        id = attribs.pop('id')
        attribs['battery_capacity'] = float(attribs['battery_capacity'])
        attribs['initial_soc'] = float(attribs['initial_soc'])
        if id in vehicles:
            elem_vehicle_type = attribs.pop('vehicle_type')
            vehicle_type = vehicles[id].vehicle_type
            if elem_vehicle_type != vehicle_type.id:
                raise RuntimeError(f'Electric vehicle: {id} has mis-matched vehicle type '
                                   f'defined: {elem_vehicle_type} != {vehicle_type.id}')
        else:
            vehicle_type = VehicleType(id=attribs.pop('vehicle_type'))
        vehicles[id] = ElectricVehicle(id=id, vehicle_type=vehicle_type, **attribs)
    return vehicles


def load_pickle(path):
    with open(path, 'rb') as file:
        return pickle.load(file)
