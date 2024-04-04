import logging
from typing import Optional, Union

import pandas as pd

import pam.activity as activity
import pam.core as core
import pam.utils as utils


def load_travel_diary(
    trips: Union[pd.DataFrame, str],
    persons_attributes: Union[pd.DataFrame, str, None] = None,
    hhs_attributes: Union[pd.DataFrame, str, None] = None,
    sample_perc: Optional[float] = None,
    tour_based: bool = True,
    from_to: bool = False,
    include_loc: bool = False,
    sort_by_seq: Optional[bool] = None,
    trip_freq_as_person_freq: bool = False,
    trip_freq_as_hh_freq: bool = False,
) -> core.Population:
    """Turn standard tabular data inputs (travel survey and attributes) into core population format.

    Args:
      trips (Union[pd.DataFrame, str]):
      persons_attributes (Union[pd.DataFrame, str, None], optional): Defaults to None.
      hhs_attributes (Union[pd.DataFrame, str, None], optional): Defaults to None.
      sample_perc (float, optional): If different to None, it samples the travel population by the corresponding percentage. Defaults to None.
      tour_based (bool, optional): Set to False to force a simpler trip-based purpose parser. Defaults to True.
      from_to (bool, optional): Set to True to force the from-to purpose parser (requires 'oact' and 'dact' trips columns). Defaults to False.
      include_loc (bool, optional): If True, include location data as shapely Point geometries ('start_loc' and 'end_loc' trips columns). Defaults to False.
      sort_by_seq (bool, optional): If not None, force trip sorting as True or False. Defaults to None.
      trip_freq_as_person_freq (bool, optional): Defaults to False.
      trip_freq_as_hh_freq (bool, optional): Defaults to False.

    Returns:
      core.Population:
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

    if ("oact" in trips.columns and "dact" in trips.columns) or from_to:
        logger.warning("Using from-to activity parser using 'oact' and 'dact' columns")
        from_to = True

        # check that trips diary has required fields
        missing = {"pid", "ozone", "dzone", "oact", "dact", "mode", "tst", "tet"} - set(
            trips.columns
        )

        if missing:
            raise UserWarning(f"Input trips_diary missing required column names: {missing}.")

    else:
        if tour_based:
            logger.warning("Using tour based purpose parser (recommended)")
        else:
            logger.warning(
                """
Using simple trip based purpose parser, this assumes first activity is 'home'.
If you do not wish to assume this, try setting 'tour_based' = True (default).
"""
            )

        # check that trips diary has required fields
        missing = {"pid", "ozone", "dzone", "purp", "mode", "tst", "tet"} - set(trips.columns)
        if missing:
            raise UserWarning(f"Input trips_diary missing required column names: {missing}.")

    if sort_by_seq and "seq" not in trips.columns:
        raise UserWarning(
            """
    You must include a trips 'seq' column if you wish to sort trips:
    Either include a 'seq' column or use the existing ordering by
    setting 'sort_by_seq' = False/None (default).
    """
        )

    if include_loc and not all(x in trips.columns for x in ["start_loc", "end_loc"]):
        raise UserWarning(
            """
    You must include a trips 'start_loc' and 'end_loc' column if you wish to use precise locations:
    Either include a 'start_loc' and 'end_loc' column or set 'include_loc' = False (default).
    Note that these columns must be shapely Point geometries.
    """
        )

    if trip_freq_as_person_freq:  # use trip freq as person freq
        if "freq" not in trips.columns:
            raise UserWarning(
                """
                You have opted to use 'trip_freq_as_person_freq' but cannot build this mapping:
                Please check 'freq' is included in the trips_diary input.
                """
            )

        logger.info("Loading person freq ('freq') from trips_diary freq input.")
        pid_freq_map = dict(zip(trips.pid, trips.freq))  # this will take last freq from trips

        if persons_attributes is None:
            logger.info("Building new person attributes dataframe to hold person frequency.")
            persons_attributes = pd.DataFrame(
                {"pid": list(pid_freq_map.keys()), "freq": list(pid_freq_map.values())}
            )
        else:
            logger.info("Adding freq to person attributes using trip frequency.")
            persons_attributes["freq"] = persons_attributes.pid.map(pid_freq_map)

        trips.drop("freq", axis=1, inplace=True)

    if trip_freq_as_hh_freq:
        if "freq" not in trips.columns:
            raise UserWarning(
                """
                You have opted to use 'trip_freq_as_hh_freq' but cannot build this mapping:
                Please check 'freq' is included in the trips_diary input.
                """
            )
        if "hid" not in trips.columns:
            raise UserWarning(
                """
                You have opted to use 'trip_freq_as_hh_freq' but cannot build this mapping:
                Please check 'hid' is included in the trips_diary input.
                """
            )

        logger.info("Loading houshold freq ('freq') from trips_diary freq input.")
        hid_freq_map = dict(zip(trips.hid, trips.freq))  # this will take last freq from trips

        if hhs_attributes is None:
            logger.info("Building new household attributes dataframe to hold houshold frequency.")
            hhs_attributes = pd.DataFrame(
                {"hid": list(hid_freq_map.keys()), "freq": list(hid_freq_map.values())}
            )
        else:
            logger.info("Adding freq to household attributes using trip frequency.")
            hhs_attributes["freq"] = hhs_attributes.hid.map(hid_freq_map)

        trips.drop("freq", axis=1, inplace=True)

    # add hid to trips if not already added
    if (
        "hid" not in trips.columns
        and (persons_attributes is None or "hid" not in persons_attributes.columns)
        and (hhs_attributes is None or "pid" not in hhs_attributes.columns)
    ):
        logger.warning(
            """
            No household entities found, households will be composed of individual persons using 'pid':
            If you wish to correct this, please add 'hid' to either the trips or persons_attributes inputs.
            """
        )
        trips["hid"] = trips.pid

    # check that person_attributes has required fields if used
    if persons_attributes is not None:
        if "pid" not in persons_attributes.columns and not persons_attributes.index.name == "pid":
            raise UserWarning(
                "Input person_attributes dataframe missing required unique identifier column: 'pid'."
            )

        if "hid" not in persons_attributes and "hid" in trips:
            logger.warning("Adding pid->hh mapping to persons_attributes from trips.")
            mapping = dict(zip(trips.pid, trips.hid))
            persons_attributes["hid"] = persons_attributes.pid.map(mapping)

        if "hzone" not in persons_attributes.columns and "hid" in persons_attributes.columns:
            if hhs_attributes is not None and "hzone" in hhs_attributes:
                logger.warning("Adding home locations to persons attributes using hhs_attributes.")
                mapping = dict(zip(hhs_attributes.hid, hhs_attributes.hzone))
                persons_attributes["hzone"] = persons_attributes.hid.map(mapping)
            elif "hzone" in trips and "hid" in trips:
                logger.warning(
                    "Adding home locations to persons attributes using trips attributes."
                )
                mapping = dict(zip(trips.hid, trips.hzone))
                persons_attributes["hzone"] = persons_attributes.hid.map(mapping)

    # check if hh_attributes are being used
    if hhs_attributes is not None:
        if "hid" not in hhs_attributes.columns and not hhs_attributes.index.name == "hid":
            raise UserWarning(
                "Input hh_attributes dataframe missing required unique identifier column: 'hid'."
            )

        if "hid" in trips.columns:
            logger.info("Using person to household mapping from trips_diary data")
            if persons_attributes is not None and "hid" not in persons_attributes.columns:
                logger.info(
                    "Loading person to household mapping for person_attributes from trips data"
                )
                person_hh_mapping = dict(zip(trips.pid, trips.hid))
                persons_attributes["hid"] = persons_attributes.pid.map(person_hh_mapping)

        elif persons_attributes is not None and "hid" in persons_attributes.columns:
            logger.info("Loading person to household mapping from person_attributes data")
            person_hh_mapping = dict(zip(persons_attributes.pid, persons_attributes.hid))
            trips["hid"] = trips.pid.map(person_hh_mapping)

        else:
            raise UserWarning(
                """
            Household attributes found but failed to build person to household mapping from provided inputs:
            Please provide a household ID field ('hid') in either the trips_diary or person_attributes inputs.
            """
            )

        if "hzone" not in hhs_attributes.columns:
            if (
                persons_attributes is not None
                and "hzone" in persons_attributes
                and "hid" in persons_attributes.columns
            ):
                logger.warning("Adding home locations to hhs attributes using persons_attributes.")
                mapping = dict(zip(persons_attributes.hid, persons_attributes.hzone))
                hhs_attributes["hzone"] = hhs_attributes.hid.map(mapping)
            elif "hzone" in trips and "hid" in trips:
                logger.warning("Adding home locations to hhs attributes using trips attributes.")
                mapping = dict(zip(trips.hid, trips.hzone))
                hhs_attributes["hzone"] = hhs_attributes.hid.map(mapping)

    # add hzone to trips_diary
    if "hzone" not in trips.columns:
        if hhs_attributes is not None and "hzone" in hhs_attributes.columns:
            logger.info("Loading household area ('hzone') from hh_attributes input.")
            hh_mapping = dict(zip(hhs_attributes.hid, hhs_attributes.hzone))
            trips["hzone"] = trips.hid.map(hh_mapping)
        elif (
            persons_attributes is not None
            and "hzone" in persons_attributes.columns
            and "hid" in persons_attributes.columns
        ):
            logger.info("Loading household area ('hzone') from person_attributes input.")
            hh_mapping = dict(zip(persons_attributes.hid, persons_attributes.hzone))
            trips["hzone"] = trips.hid.map(hh_mapping)
        else:
            logger.warning(
                """
        Unable to load household area ('hzone') - not found in trips_diary or unable to build from attributes.
        Pam will try to infer home location from activities, but this behaviour is not recommended.
        """
            )

    # Add an empty frequency fields if required
    if "freq" not in trips.columns:
        logger.warning("Using freq of 'None' for all trips.")
        trips["freq"] = None

    if persons_attributes is not None and "freq" not in persons_attributes.columns:
        logger.warning("Using freq of 'None' for all persons.")
        persons_attributes["freq"] = None

    if hhs_attributes is not None and "freq" not in hhs_attributes.columns:
        logger.warning("Using freq of 'None' for all households.")
        hhs_attributes["freq"] = None

    if sample_perc is not None:
        if "freq" not in trips.columns:
            raise UserWarning(
                f"""
                You have opted to use a sample ({sample_perc}, but this option requires that trips frequencies are set:):
                Please add a 'freq' column to the trips dataframe or remove sampling (set 'sample_perc' = None).
                """
            )
        trips = sample_population(
            trips=trips, sample_perc=sample_perc, weight_col="freq"
        )  # sample the travel population

    logger.debug("Resetting trips index if required")
    if trips.index.name is not None:
        persons_attributes.reset_index(inplace=True)

    if persons_attributes is not None:
        logger.debug("Setting persons_attributes index to pid")
        if persons_attributes.index.name is None:
            persons_attributes.set_index("pid", inplace=True)
        elif not persons_attributes.index.name == "pid":
            persons_attributes = persons_attributes.reset_index().set_index("pid")

    if hhs_attributes is not None:
        logger.debug("Setting households_attributes index to hid")
        if hhs_attributes.index.name is None:
            hhs_attributes.set_index("hid", inplace=True)
        elif not hhs_attributes.index.name == "hid":
            hhs_attributes = hhs_attributes.reset_index().set_index("hid")

    if from_to:
        logger.debug("Initiating from-to parser.")
        return from_to_travel_diary_read(
            trips=trips,
            persons_attributes=persons_attributes,
            hhs_attributes=hhs_attributes,
            include_loc=include_loc,
            sort_by_seq=sort_by_seq,
        )

    if tour_based:
        logger.debug("Initiating tour-based parser.")
        return tour_based_travel_diary_read(
            trips=trips,
            persons_attributes=persons_attributes,
            hhs_attributes=hhs_attributes,
            include_loc=include_loc,
            sort_by_seq=sort_by_seq,
        )

    logger.debug("Initiating trip-based parser.")
    return trip_based_travel_diary_read(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes,
        include_loc=include_loc,
        sort_by_seq=sort_by_seq,
    )


def build_population(
    trips: Optional[pd.DataFrame] = None,
    persons_attributes: Optional[pd.DataFrame] = None,
    hhs_attributes: Optional[pd.DataFrame] = None,
) -> core.Population:
    """Build a population of households and persons (without plans).

    Built from available trips, persons_attributes and households_attributes data.
    Details of required table formats are in the README.

    Args:
      trips (Optional[pd.DataFrame]): trips table. Defaults to None.
      persons_attributes (Optional[pd.DataFrame]): persons attributes table. Defaults to None.
      hhs_attributes (Optional[pd.DataFrame]): households attributes table. Defaults to None.

    Returns:
      pam.Population: population object

    """
    population = core.Population()
    add_hhs_from_hhs_attributes(population=population, hhs_attributes=hhs_attributes)
    add_hhs_from_persons_attributes(population=population, persons_attributes=persons_attributes)
    add_hhs_from_trips(population=population, trips=trips)
    add_persons_from_persons_attributes(
        population=population, persons_attributes=persons_attributes
    )
    add_persons_from_trips(population=population, trips=trips)

    return population


def add_hhs_from_hhs_attributes(
    population: core.Population, hhs_attributes: Optional[pd.DataFrame] = None
):
    logger = logging.getLogger(__name__)

    if hhs_attributes is None:
        return None

    logger.info("Adding hhs from hhs_attributes")
    for hid, hh in hhs_attributes.groupby("hid"):
        if hid not in population.households:
            hh_attributes = hhs_attributes.loc[hid].to_dict()
            household = core.Household(
                hid,
                attributes=hh_attributes,
                freq=hh_attributes.pop("freq", None),
                area=hh_attributes.pop("hzone", None),
            )
            population.add(household)


def add_hhs_from_persons_attributes(
    population: core.Population, persons_attributes: Optional[pd.DataFrame] = None
):
    logger = logging.getLogger(__name__)

    if persons_attributes is None or "hid" not in persons_attributes.columns:
        return None

    if "hzone" in persons_attributes.columns:
        hzone_lookup = persons_attributes.groupby("hid").head(1).set_index("hid").hzone.to_dict()
    else:
        hzone_lookup = {}

    logger.info("Adding hhs from persons_attributes")
    for hid, hh_data in persons_attributes.groupby("hid"):
        if hid not in population.households:
            hzone = hzone_lookup.get(hid)
            household = core.Household(hid, area=hzone)
            population.add(household)


def add_hhs_from_trips(population: core.Population, trips: Optional[pd.DataFrame] = None):
    logger = logging.getLogger(__name__)

    if trips is None or "hid" not in trips.columns:
        return None

    logger.info("Adding hhs from trips")
    for hid, hh_data in trips.groupby("hid"):
        if hid not in population.households:
            hzone = hh_data.iloc[0].to_dict().get("hzone")
            household = core.Household(hid, area=hzone)
            population.add(household)


def add_persons_from_persons_attributes(
    population: core.Population, persons_attributes: Optional[pd.DataFrame] = None
):
    logger = logging.getLogger(__name__)

    if persons_attributes is None or "hid" not in persons_attributes.columns:
        return None

    persons_attributes_dict = (
        persons_attributes.reset_index().set_index(["hid", "pid"]).to_dict("index")
    )

    logger.info("Adding persons from persons_attributes")
    for hid, hh_data in persons_attributes.groupby("hid"):
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
                home_area=person_attributes.get("hzone", None),
                freq=person_attributes.pop("freq", None),
            )
            household.add(person)


def add_persons_from_trips(population: core.Population, trips: Optional[pd.DataFrame] = None):
    logger = logging.getLogger(__name__)

    if trips is None or "hid" not in trips.columns:
        return None

    logger.info("Adding persons from trips")
    for (hid, pid), hh_person_data in trips.groupby(["hid", "pid"]):
        household = population.households.get(hid)
        if household is None:
            logger.warning(f"Failed to find household {hid} in population - unable to add person.")
            continue
        if pid in household.people:
            continue
        person = core.Person(pid, home_area=hh_person_data.iloc[0].to_dict().get("hzone"))
        household.add(person)


def tour_based_travel_diary_read(
    trips: pd.DataFrame,
    persons_attributes: Optional[pd.DataFrame] = None,
    hhs_attributes: Optional[pd.DataFrame] = None,
    include_loc: bool = False,
    sort_by_seq: Optional[bool] = None,
) -> core.Population:
    """Complex travel diray reader.

    Will try to infer home activity and tour based purposes.

    Args:
        trips (pd.DataFrame):
        persons_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        hhs_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        include_loc (bool, optional): optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns). Defaults to False.
        sort_by_seq (Optional[bool], optional): optionally force trip sorting as True or False. Defaults to None.

    Returns:
        core.Population:
    """
    population = build_population(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and "seq" in trips.columns:
        sort_by_seq = True
    if "seq" not in trips.columns:
        seq = trips.groupby(["hid", "pid"]).cumcount()
        trips = trips.assign(seq=seq.values)

    trips = trips.set_index(["hid", "pid", "seq"])

    if sort_by_seq:
        trips = trips.sort_index()

    for hid, household in population:
        for pid, person in household:
            try:
                person_trips = trips.loc[hid, pid]
            except KeyError:
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

            for seq, trip in person_trips.iterrows():
                start_loc = None
                end_loc = None

                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc

                person.add(
                    activity.Leg(
                        seq=seq,
                        purp=trip.purp.lower(),
                        mode=trip["mode"].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        distance=trip.get("distance"),
                        freq=trip.freq,
                    )
                )

                person.add(
                    activity.Activity(
                        seq=seq + 1,
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
    persons_attributes: Optional[pd.DataFrame] = None,
    hhs_attributes: Optional[pd.DataFrame] = None,
    include_loc: bool = False,
    sort_by_seq: Optional[bool] = None,
) -> core.Population:
    """Turn Activity Plan tabular data inputs into core population format.

    Tabular data inputs are derived from travel survey and attributes.

    This is a variation of the standard load_travel_diary() method because it does not require activity inference.
    However all plans are expected to be tour based, so assumed to start and end at home.
    We expect broadly the same data schema except rather than trip 'purpose' we use trips 'activity'.

    Args:
        trips (pd.DataFrame):
        persons_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        hhs_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        include_loc (bool, optional): optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns). Defaults to False.
        sort_by_seq (Optional[bool], optional): optionally force trip sorting as True or False. Defaults to None.

    Returns:
        core.Population:
    """

    population = build_population(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and "seq" in trips.columns:
        sort_by_seq = True
    if "seq" not in trips.columns:
        seq = trips.groupby(["hid", "pid"]).cumcount()
        trips = trips.assign(seq=seq.values)

    trips = trips.set_index(["hid", "pid", "seq"])

    if sort_by_seq:
        trips = trips.sort_index()

    for hid, household in population:
        for pid, person in household:
            try:
                person_trips = trips.loc[hid, pid]
            except KeyError:
                person.stay_at_home()
                continue

            household.location.area or person_trips.hzone.iloc[0]
            origin_area = person_trips.ozone.iloc[0]

            loc = None
            if include_loc:
                loc = person_trips.start_loc.iloc[0]

            person.add(
                activity.Activity(
                    seq=0, act="home", area=origin_area, loc=loc, start_time=utils.parse_time(0)
                )
            )

            for seq, trip in person_trips.iterrows():
                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc
                purpose = trip.purp.lower()

                person.add(
                    activity.Leg(
                        seq=seq,
                        purp=purpose,
                        mode=trip["mode"].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        distance=trip.get("distance"),
                    )
                )

                person.add(
                    activity.Activity(
                        seq=seq + 1,
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
    persons_attributes: Optional[pd.DataFrame] = None,
    hhs_attributes: Optional[pd.DataFrame] = None,
    include_loc: bool = False,
    sort_by_seq: Optional[bool] = False,
) -> core.Population:
    """Turn Diary Plan tabular data inputs into core population format.

    Tabular data derived from travel survey and attributes.

    This is a variation of the standard load_travel_diary() method because it does not require activity inference or home location.
    We expect broadly the same data schema except rather than purp (purpose) we use trips oact (origin activity) and dact (destination activity).

    Args:
        trips (pd.DataFrame):
        persons_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        hhs_attributes (Optional[pd.DataFrame], optional): Defaults to None.
        include_loc (bool, optional): optionally include location data as shapely Point geometries ('start_loc' and 'end_loc' columns) (Default value = False). Defaults to False.
        sort_by_seq (Optional[bool], optional): optionally force trip sorting as True or False. Defaults to False.

    Returns:
        core.Population:
    """
    logger = logging.getLogger(__name__)

    population = build_population(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )

    if sort_by_seq is None and "seq" in trips.columns:
        sort_by_seq = True
    if "seq" not in trips.columns:
        seq = trips.groupby(["hid", "pid"]).cumcount()
        trips = trips.assign(seq=seq.values)

    trips = trips.set_index(["hid", "pid", "seq"])

    if sort_by_seq:
        trips = trips.sort_index()

    for hid, household in population:
        for pid, person in household:
            try:
                person_trips = trips.loc[hid, pid]
            except KeyError:
                person.stay_at_home()
                continue

            first_act = person_trips.iloc[0].oact.lower()
            if not first_act == "home":
                logger.warning(
                    f" Person pid:{pid} hid:{hid} plan does not start with 'home' activity: {first_act}"
                )

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

            for seq, trip in person_trips.iterrows():
                start_loc = None
                end_loc = None
                if include_loc:
                    start_loc = trip.start_loc
                    end_loc = trip.end_loc
                purpose = trip.dact.lower()

                person.add(
                    activity.Leg(
                        seq=seq,
                        purp=purpose,
                        mode=trip["mode"].lower(),
                        start_area=trip.ozone,
                        end_area=trip.dzone,
                        start_loc=start_loc,
                        end_loc=end_loc,
                        start_time=utils.parse_time(trip.tst),
                        end_time=utils.parse_time(trip.tet),
                        distance=trip.get("distance"),
                    )
                )

                person.add(
                    activity.Activity(
                        seq=seq + 1,
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


def sample_population(
    trips_df: pd.DataFrame,
    sample_perc: float,
    attributes_df: Optional[pd.DataFrame] = None,
    weight_col: str = "freq",
) -> pd.DataFrame:
    """Return the trips of a random sample of the travel population.

    We merge the trips and attribute datasets to enable probability weights based on population demographics.

    Args:
        trips_df (pd.DataFrame): Trips dataset
        sample_perc (float): Sampling percentage
        attributes_df (Optional[pd.DataFrame], optional): Population attributes dataset. Defaults to None.
        weight_col (str, optional): The field to use for probability weighting. Defaults to "freq".

    Returns:
        pd.DataFrame:  a sampled version of the `trips_df` dataframe
    """
    if attributes_df is not None:
        sample_pids = (
            trips_df.groupby("pid")[["freq"]]
            .sum()
            .join(attributes_df, how="left")
            .sample(frac=sample_perc, weights=weight_col)
            .index
        )
    else:
        sample_pids = (
            trips_df.groupby("pid")[["freq"]]
            .sum()
            .sample(frac=sample_perc, weights=weight_col)
            .index
        )

    return trips_df[trips_df.pid.isin(sample_pids)]
