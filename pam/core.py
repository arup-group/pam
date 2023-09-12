from __future__ import annotations

import copy
import logging
import pickle
import random
from collections import defaultdict
from collections.abc import Iterator
from typing import Any, Optional, Union

import geopandas as gpd
import pandas as pd
import plotly.graph_objs as go

import pam.activity as activity
import pam.plot as plot
from pam import (
    PAMInvalidTimeSequenceError,
    PAMSequenceValidationError,
    PAMValidationLocationsError,
    PAMVehicleIdError,
    variables,
    write,
)
from pam.location import Location
from pam.vehicles import ElectricVehicle, Vehicle, VehicleManager, VehicleType


class Population:
    def __init__(self, name: str = None) -> None:
        """Class to define a population.

        Args:
            name (str, optional): Name of population. Defaults to None.
        """
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.households = {}
        self._vehicles_manager = VehicleManager()

    def add(self, target: list[Union[Household, Person, list]]) -> None:
        """Add houeshold/person, or a list of households/persons to the population.

        Args:
            target (list[Union[Household, Person, list]]):
                Can be any arbitrary nesting of lists, as long as the deepest nesting includes only Houeshold and Person objects

        Raises:
            UserWarning: Only Household and Person objects allowed
        """
        if isinstance(target, list):
            for hh in target:
                self.add(hh)
        elif isinstance(target, Household):
            self.households[target.hid] = target
        elif isinstance(target, Person):
            self.logger.debug(
                (
                    "Directly adding a Person to a Population requires a Household.",
                    f"Auto creating a household {target.pid} for person {target.pid}, check this is intended.",
                )
            )
            self.add(Household(hid=target.pid))
            self.households[target.pid].add(target)
        else:
            raise UserWarning(
                f"Expected instance of Household, list or Person, not: {type(target)}"
            )

    def get(self, hid, default=None):
        return self.households.get(hid, default)

    def __getitem__(self, hid):
        return self.households[hid]

    def __iter__(self):
        for hid, household in self.households.items():
            yield hid, household

    def people(self):
        """Iterator for people in poulation, returns hid, pid and Person."""
        for hid, household in self.households.items():
            for pid, person in household.people.items():
                yield hid, pid, person

    def plans(self) -> Iterator[activity.Plan]:
        """Iterator for plans in poulation."""
        for hid, household in self.households.items():
            for pid, person in household.people.items():
                yield person.plan

    @property
    def population(self):
        self.logger.info("Returning un weighted person count.")
        return len([1 for hid, pid, person in self.people()])

    def __len__(self):
        return self.population

    def __contains__(self, other):
        if isinstance(other, Household):
            for _, hh in self:
                if other == hh:
                    return True
            return False
        if isinstance(other, Person):
            for _, _, person in self.people():
                if other == person:
                    return True
            return False
        raise UserWarning(
            f"Cannot check if population contains object type: {type(other)}, please provide a Household or Person."
        )

    def __eq__(self, other: Population):
        """Check for equality of two populations, equality is based on equal attributes and activity plans of all household and household members. Identifiers (eg hid and pid) are disregarded."""
        if not isinstance(other, Population):
            raise UserWarning(
                f"Cannot compare population to non population: ({type(other)}), please provide a Population."
            )
        if not len(self) == len(other):
            return False
        if not self.stats == other.stats:
            return False
        used = []
        for _, hh in self:
            for hid, hh2 in other:
                if hid in used:
                    continue
                if hh == hh2:
                    used.append(hid)
                    break
                return False
        return True

    @property
    def num_households(self):
        return len([1 for hid, hh in self.households.items()])

    @property
    def size(self):
        return self.freq

    @property
    def freq(self):
        frequencies = [hh.freq for hh in self.households.values()]
        if None in frequencies:
            return None
        return sum(frequencies)

    @property
    def activity_classes(self):
        acts = set()
        for _, _, p in self.people():
            acts.update(p.activity_classes)
        return acts

    @property
    def mode_classes(self):
        modes = set()
        for _, _, p in self.people():
            modes.update(p.mode_classes)
        return modes

    @property
    def subpopulations(self):
        subpopulations = set()
        for _, _, p in self.people():
            subpopulations.add(p.subpopulation)
        return subpopulations

    @property
    def attributes(self, show: int = 10) -> dict:
        attributes = defaultdict(set)
        for _, hh in self.households.items():
            for k, v in hh.attributes.items():
                attributes[k].add(v)
            for _, p in hh.people.items():
                for k, v in p.attributes.items():
                    attributes[k].add(str(v))
        for k, v in attributes.items():
            if len(v) > show:
                attributes[k] = set(list(attributes[k])[:show])
        return dict(attributes)

    def rebuild_vehicles_manager(self):
        """
        (Re)build vehicle population from persons. This method adds all Population vehicles from each
        Person and adds them to the Population.vehicles_manager. This method is used by write.matsim
        to write regular vehicles and electric vehicles to MATSim xml formats.
        """
        self._vehicles_manager.clear_vehs()
        self.update_vehicles_manager()

    def update_vehicles_manager(self):
        """
        Update vehicle population from persons.
        """
        vehs = {}
        for _, _, _, veh in self.vehicles():
            if veh.vid in vehs:
                raise PAMVehicleIdError("Failed to build due to duplicate vehicle id: {veh.vid}")
            vehs[veh.vid] = veh
        self._vehicles_manager._vehicles.update(vehs)
        if not self._vehicles_manager.is_consistent():
            raise UserWarning("Failed consistency check refer to logs.")

    def check_vehicles(self) -> bool:
        """Checks that all person vehicles have types defined by vehicles manager.

        Raises:
            PAMVehicleIdError: Undefined vehicle type in population.

        Returns:
            bool: Return true if all vehicle types are defined.
        """
        veh_types = set(self._vehicles_manager._veh_types.keys())
        for _, _, _, veh in self.vehicles():
            if veh.type_id not in veh_types:
                raise PAMVehicleIdError(
                    f"Failed to find veh type of id '{veh.type_id}', specified for veh id '{veh.vid}'."
                )
        return True

    @property
    def vehicle_types(self) -> dict[str, VehicleType]:
        """
        Returns:
            dist[str, VehicleType]: Mapping of vehicle type id to vehicle type data.
        """
        return self._vehicles_manager._veh_types

    def vehicles(self) -> Iterator[str, str, str, Vehicle]:
        """Return iterator of all vehicles in population, prepended with household id, person id
        and mode.

        Yields:
            Iterator[str, str, str, Vehicle]: Iterator of (hid, pid, mode, vehicle)
        """
        for hid, pid, p in self.people():
            for mode, veh in p.vehicles.items():
                yield hid, pid, mode, veh

    def evs(self) -> Iterator[str, str, str, ElectricVehicle]:
        """Return iterator of all electric vehicles in population, prepended with household id,
        person id and mode.

        Yields:
            Iterator[str, str, str, ElectricVehicle]: Iterator of (hid, pid, mode, vehicle)
        """
        for hid, pid, p in self.people():
            for mode, veh in p.evs():
                yield hid, pid, mode, veh

    @property
    def has_vehicles(self) -> bool:
        return next(self.vehicles(), None) is not None

    @property
    def has_electric_vehicles(self):
        return next(self.evs(), None) is not None

    def add_veh_type(self, vehicle_type: VehicleType):
        """Add a vehicle type to the population vehicles manager.

        Args:
            vehicle_type (VehicleType): Vehicle type to be added.
        """
        self._vehicles_manager.add_type(vehicle_type)

    def remove_vehicle_type(self, tid: str):
        """Remove vehicle type from vehicles manager.

        Args:
            tid (str): Vehicle type id.
        """
        self._vehicles_manager.remove_type(tid)

    def add_veh(self, hid: str, pid: str, mode: str, vehicle: Vehicle):
        """Add vehicle of given mode to person, based on hid and pid. Method checks that id is unique and vehicle type is available, otherwise raises UserWarning.

        Args:
            hid (str): Household id
            pid (str): Person id
            mode (str): Mode of vehicle
            vehicle (Vehicle): Vehicle to add

        Raises:
            UserWarning: Duplicate id.
            UserWarning: Unknown vehicle type.

        """
        if vehicle.type_id not in self._vehicles_manager._veh_types:
            raise UserWarning(f"Unable to add vehicle with unknown type: '{vehicle.type_id}'.")
        person_vehicles = self.households[hid][pid].vehicles
        if not (
            person_vehicles.get(mode) and person_vehicles[mode].vid == vehicle.vid
        ):  # assume not replacing existing
            # so check for duplicates
            if vehicle.vid in set([v.vid for _, _, _, v in self.vehicles()]):
                raise UserWarning(
                    f"Unable to add vehicle with duplicate vehicle id (vid): {vehicle.vid}"
                )
        person_vehicles[mode] = vehicle

    def random_household(self):
        return self.households[random.choice(list(self.households))]

    def random_person(self):
        hh = self.random_household()
        return hh.random_person()

    @property
    def stats(self):
        num_households = 0
        num_people = 0
        num_activities = 0
        num_legs = 0
        for hid, household in self:
            num_households += 1
            for pid, person in household:
                num_people += 1
                num_activities += person.num_activities
                num_legs += person.num_legs
        return {
            "num_households": num_households,
            "num_people": num_people,
            "num_activities": num_activities,
            "num_legs": num_legs,
        }

    def legs_df(self) -> pd.DataFrame:
        """Extract tabular record of population legs.

        Returns:
            pd.DataFrame: record of legs
        """
        df = []
        for hid, pid, person in self.people():
            for seq, leg in enumerate(person.legs):
                record = {
                    "pid": pid,
                    "hid": hid,
                    "hzone": person.home,
                    "ozone": leg.start_location.area,
                    "dzone": leg.end_location.area,
                    "oloc": leg.start_location,
                    "dloc": leg.end_location,
                    "seq": seq,
                    "purp": leg.purp,
                    "mode": leg.mode,
                    "tst": leg.start_time.time(),
                    "tet": leg.end_time.time(),
                    # duration in minutes
                    "duration": leg.duration / pd.Timedelta(minutes=1),
                    "euclidean_distance": leg.euclidean_distance,
                    "freq": person.freq,
                }
                # add person attributes
                record = {**record, **dict(person.attributes)}
                df.append(record)
        df = pd.DataFrame(df)
        self.add_fields(df)
        return df

    def trips_df(self) -> pd.DataFrame:
        """Extract tabular record of population legs.

        Returns:
            pd.DataFrame: record of legs
        """
        df = []
        for hid, pid, person in self.people():
            for seq, trip in enumerate(person.plan.trips()):
                record = {
                    "pid": pid,
                    "hid": hid,
                    "hzone": person.home,
                    "ozone": trip.start_location.area,
                    "dzone": trip.end_location.area,
                    "oloc": trip.start_location,
                    "dloc": trip.end_location,
                    "seq": seq,
                    "purp": trip.purp,
                    "mode": trip.mode,
                    "tst": trip.start_time.time(),
                    "tet": trip.end_time.time(),
                    # duration in minutes
                    "duration": trip.duration / pd.Timedelta(minutes=1),
                    "euclidean_distance": trip.euclidean_distance,
                    "freq": person.freq,
                }
                # add person attributes
                record = {**record, **dict(person.attributes)}
                df.append(record)

        df = pd.DataFrame(df)
        self.add_fields(df)
        return df

    @staticmethod
    def add_fields(df: pd.DataFrame) -> None:
        """Add extra fields used for benchmarking in place.

        Args:
            df (pd.DataFrame):
        """
        df["personhrs"] = df["freq"] * df["duration"] / 60
        df["departure_hour"] = df.tst.apply(lambda x: x.hour)
        df["arrival_hour"] = df.tet.apply(lambda x: x.hour)
        df["euclidean_distance_category"] = pd.cut(
            df.euclidean_distance,
            bins=[0, 1, 5, 10, 25, 50, 100, 200, 999999],
            labels=[
                "0 to 1 km",
                "1 to 5 km",
                "5 to 10 km",
                "10 to 25 km",
                "25 to 50 km",
                "50 to 100 km",
                "100 to 200 km",
                "200+ km",
            ],
        )
        df["duration_category"] = pd.cut(
            df.duration,
            bins=[0, 5, 10, 15, 30, 45, 60, 90, 120, 999999],
            labels=[
                "0 to 5 min",
                "5 to 10 min",
                "10 to 15 min",
                "15 to 30 min",
                "30 to 45 min",
                "45 to 60 min",
                "60 to 90 min",
                "90 to 120 min",
                "120+ min",
            ],
        )

    def build_travel_geodataframe(self, **kwargs) -> gpd.GeoDataFrame:
        """Builds geopandas.GeoDataFrame for travel Legs found for all persons in the Population.

        Keyword Args: Keyword arguments for plot.build_person_travel_geodataframe.
            from_epsg (str): coordinate system the plans are currently in
            to_epsg (str): coordinate system you want the geo dataframe to be projected to, optional, you need to specify from_epsg as well to use this.

        Returns:
            geopandas.GeoDataFrame:  with columns for household id (hid) and person id (pid)
        """
        gdf = None
        for hid, household in self.households.items():
            _gdf = household.build_travel_geodataframe(**kwargs)
            if gdf is None:
                gdf = _gdf
            else:
                gdf = pd.concat([gdf, _gdf])
        gdf = gdf.sort_values(["hid", "pid", "seq"]).reset_index(drop=True)
        return gdf

    def plot_travel_plotly(self, epsg: str = "epsg:4326", **kwargs) -> go.Figure:
        """Plot travel plans.

        Args:
            epsg (str, optional): coordinate system the plans spatial information is in, e.g. 'epsg:27700'. Defaults to "epsg:4326".

        Keyword Args: Keyword arguments for plot.plot_travel_plans
            gdf (geopandas.GeoDataFrame): geopandas.GeoDataFrame generated by build_person_travel_geodataframe
            groupby (list): optional argument for splitting traces in the plot.
            colour_by (str): argument for specifying what the colour should correspond to in the plot, travel mode by default.
            cmap (dict): optional argument, useful to pass if generating a number of plots and want to keep colour scheme consistent.
            mapbox_access_token (str): required to generate the plot (see https://docs.mapbox.com/help/how-mapbox-works/access-tokens/).

        Returns:
            go.Figure: Plotly figure object.
        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"), **kwargs
        )

    def fix_plans(self, crop: bool = True, times=True, locations=True):
        for _, _, person in self.people():
            if crop:
                person.plan.crop()
            if times:
                person.plan.fix_time_consistency()
            if locations:
                person.plan.fix_location_consistency()

    def validate(self):
        for hid, pid, person in self.people():
            person.validate()

    def print(self):
        print(self)
        for _, household in self:
            household.print()

    def pickle(self, path: str):
        with open(path, "wb") as file:
            pickle.dump(self, file)

    def to_csv(self, dir: str, crs=None, to_crs: str = "EPSG:4326"):
        write.to_csv(self, dir, crs, to_crs)

    def __str__(self):
        return f"Population: {self.population} people in {self.num_households} households."

    def __iadd__(self, other):
        """Unsafe addition with assignment (no guarantee of unique ids)."""
        self.logger.debug(
            "Note that this method requires all identifiers from populations being combined to be unique."
        )
        if isinstance(other, Population):
            for hid, hh in other.households.items():
                self.households[hid] = copy.deepcopy(hh)
            return self
        if isinstance(other, Household):
            self.households[other.hid] = copy.deepcopy(other)
            return self
        if isinstance(other, Person):
            self.households[other.pid] = Household(other.pid)
            self.households[other.pid].people[other.pid] = copy.deepcopy(other)
            return self
        raise TypeError(
            f"Object for addition must be a Population Household or Person object, not {type(other)}"
        )

    def reindex(self, prefix: str):
        """Safely reindex all household and person identifiers in population using a prefix."""
        for hid in list(self.households):
            hh = self.households[hid]
            new_hid = prefix + str(hid)
            if new_hid in self.households:
                raise KeyError(f"Duplicate household identifier (hid): {new_hid}")

            hh.reindex(prefix)

            self.households[new_hid] = hh
            del self.households[hid]

    def combine(self, other, prefix=""):
        """Safe addition with assignment by adding a prefix to create unique pids and hids."""
        prefix = str(prefix)

        if isinstance(other, Population):
            other.reindex(prefix)
            self += other
            return None
        if isinstance(other, Household):
            other.reindex(prefix)
            self += other
            return None
        if isinstance(other, Person):
            hh = Household(other.pid)  # we create a new hh for single person
            hh.add(other)
            hh.reindex(prefix)
            self += hh
            return None
        raise TypeError(
            f"Object for addition must be a Population Household or Person object, not {type(other)}"
        )

    def sample_locs(
        self,
        sampler,
        long_term_activities: list = None,
        joint_trips_prefix: str = "escort_",
        location_override: bool = True,
    ):
        """WIP Sample household plan locs using a sampler.

        Sampler uses activity types and areas to sample locations. Note that households share
        locations for activities of the same type within the same area. Trivially this includes
        household location. But also, for example, shopping activities if they are in the same area.

        We treat escort activities (ie those prefixed by "escort_") as the escorted activity. For
        example, the sampler treats "escort_education" and "education" equally. Note that this shared
        activity sampling of location models shared facilities, but does not explicitly infer or
        model shared transport. For example there is no consideration of if trips to shared locations
        take place at the same time or from the same locations.

        After sampling Location objects are shared between shared activity locations and corresponding
        trips start and end locations. These objects are mutable, so care must be taken if making changes
        as these will impact all other persons shared locations in the household. Often this behaviour
        might be expected. For example if we change the location of the household home activity, all
        persons and home activities are impacted.

        Args:
            long_term_activities (list, optional): a list of activities for which location is only assigned once (per zone). Defaults to None
            joint_trips_prefix (str, optional): a purpose prefix used to identify escort/joint trips. Defaults to "escort_"
            location_override (bool, optional): if False, the facility sampler will retain any already-existing locations in the population.. Defaults to True
        """
        if long_term_activities is None:
            long_term_activities = variables.LONG_TERM_ACTIVITIES

        for _, household in self.households.items():
            home_loc = activity.Location(
                area=household.location.area, loc=sampler.sample(household.location.area, "home")
            )

            unique_locations = {(household.location.area, "home"): home_loc}

            for __, person in household.people.items():
                for act in person.activities:
                    # remove escort prefix from activity types.
                    if act.act[: len(joint_trips_prefix)] == joint_trips_prefix:
                        target_act = act.act[(len(joint_trips_prefix)) :]
                    else:
                        target_act = act.act

                    # assign any unique locations
                    if (act.location.area, target_act) in unique_locations:
                        location = unique_locations[(act.location.area, target_act)]
                        act.location = location
                    # sample facility
                    elif location_override or act.location.loc is None:
                        location = activity.Location(
                            area=act.location.area,
                            loc=sampler.sample(act.location.area, target_act),
                        )
                        if target_act in long_term_activities:
                            # one location per zone for long-term choices (only)
                            # short-term activities, such as shopping can visit multiple locations in the same zone
                            unique_locations[(act.location.area, target_act)] = location
                        act.location = location

                # complete the alotting activity locations to the trip starts and ends.
                for idx in range(person.plan.length):
                    component = person.plan[idx]
                    if isinstance(component, activity.Leg):
                        component.start_location = person.plan[idx - 1].location
                        component.end_location = person.plan[idx + 1].location

    def sample_locs_complex(
        self, sampler, long_term_activities: list = None, joint_trips_prefix: str = "escort_"
    ):
        """Extends sample_locs method to enable more complex and rules-based sampling.

        Keeps track of the last location and transport mode, to apply distance- and mode-based sampling rules.
        It is generally slower than sample_locs, as it loops through both activities and legs.

        Args:
            long_term_activities (list, optional):
                a list of activities for which location is only assigned once (per zone).
                Defaults to None.
            joint_trips_prefix (str, optional):
                a purpose prefix used to identify escort/joint trips.
                Defaults to "escort_".
        """
        if long_term_activities is None:
            long_term_activities = variables.LONG_TERM_ACTIVITIES

        for _, household in self.households.items():
            home_loc = activity.Location(
                area=household.location.area,
                loc=sampler.sample(
                    household.location.area,
                    "home",
                    mode=None,
                    previous_duration=None,
                    previous_loc=None,
                ),
            )
            mode = None

            unique_locations = {(household.location.area, "home"): home_loc}

            for _, person in household.people.items():
                mode = None
                previous_duration = None
                previous_loc = None

                for idx, component in enumerate(person.plan):
                    # loop through all plan elements

                    if isinstance(component, activity.Leg):
                        mode = component.mode  # keep track of last mode
                        previous_duration = component.duration

                    elif isinstance(component, activity.Activity):
                        act = component

                        # remove "escort_" from activity types.
                        # TODO: model joint trips
                        if act.act[: len(joint_trips_prefix)] == joint_trips_prefix:
                            target_act = act.act[(len(joint_trips_prefix)) :]
                        else:
                            target_act = act.act

                        if (act.location.area, target_act) in unique_locations:
                            location = unique_locations[(act.location.area, target_act)]
                            act.location = location

                        else:
                            location = activity.Location(
                                area=act.location.area,
                                loc=sampler.sample(
                                    act.location.area,
                                    target_act,
                                    mode=mode,
                                    previous_duration=previous_duration,
                                    previous_loc=previous_loc,
                                ),
                            )
                            if target_act in long_term_activities:
                                unique_locations[(act.location.area, target_act)] = location
                            act.location = location

                        previous_loc = location.loc  # keep track of previous location

                # complete the alotting activity locations to the trip starts and ends.
                for idx in range(person.plan.length):
                    component = person.plan[idx]
                    if isinstance(component, activity.Leg):
                        component.start_location = person.plan[idx - 1].location
                        component.end_location = person.plan[idx + 1].location


class Household:
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        hid,
        attributes={},
        freq=None,
        location: Optional[Location] = None,
        area=None,
        loc=None,
    ):
        self.hid = hid
        self.people = {}
        self.attributes = attributes
        self.hh_freq = freq
        if location:
            self._location = location
        else:
            self._location = Location()
        if area:  # potential overwrite
            self._location.area = area
        if loc:  # potential overwrite
            self._location.loc = loc

    def add(self, person):
        if isinstance(person, list):
            for p in person:
                self.add(p)
        elif isinstance(person, Person):
            self.people[person.pid] = person
        else:
            raise UserWarning(f"Expected instance of Person, not: {type(person)}")

    def get(self, pid, default=None):
        return self.people.get(pid, default)

    def random_person(self):
        return self.people[random.choice(list(self.people))]

    def __getitem__(self, pid):
        return self.people[pid]

    def __iter__(self):
        for pid, person in self.people.items():
            yield pid, person

    def __len__(self):
        return len(self.people)

    def __contains__(self, other_person):
        if not isinstance(other_person, Person):
            raise UserWarning(
                f"Cannot check if household contains object type: {type(other_person)}, please provide Person."
            )
        for _, person in self:
            if other_person == person:
                return True
        return False

    def __eq__(self, other):
        """Check for equality of two households, equality is based on equal attributes and activity plans of household and household members.
        Identifiers (eg hid and pid) are disregarded unless they are included in attributes.
        """
        if not isinstance(other, Household):
            self.logger.warning(f"Cannot compare household to non household: ({type(other)}).")
            return False
        if not self.attributes == other.attributes:
            return False
        if not len(self) == len(other):
            return False
        used = []
        for _, person in self:
            for pid, person2 in other:
                if pid in used:
                    continue
                if person == person2:
                    used.append(pid)
                    break
                return False
        return True

    @property
    def location(self):
        if self._location.exists:
            return self._location
        for person in self.people.values():
            if person.home.exists:
                return person.home
        self.logger.warning(f"Failed to find location for household: {self.hid}")
        return self._location

    def set_location(self, location: Location):
        """Set both hh and person home_location, but note that hhs and their persons do not share location object."""
        self._location = location
        for _, person in self:
            person.set_location(location.copy())

    def set_area(self, area):
        self._location.area = area
        for _, person in self:
            person.set_area(area)

    def set_loc(self, loc):
        self._location.loc = loc
        for _, person in self:
            person.set_loc(loc)

    @property
    def activities(self):
        for _, p in self:
            if p.plan:
                for act in p.plan.activities:
                    yield act

    @property
    def activity_classes(self):
        return set(a.act for a in self.activities)

    @property
    def legs(self):
        for _, p in self:
            if p.plan:
                for leg in p.plan.legs:
                    yield leg

    @property
    def mode_classes(self):
        return set(leg.mode for leg in self.legs)

    def get_attribute(self, key) -> set:
        """Get set of attribute values for given key, First searches hh attributes then occupants."""
        if key in self.attributes:
            return {self.attributes[key]}
        attributes = set()
        for _, person in self:
            attributes.add(person.attributes.get(key))
        return attributes

    @property
    def subpopulation(self):
        return self.get_attribute("subpopulation")

    def vehicles(self):
        for pid, p in self.people.items():
            for mode, veh in p.vehicles.items():
                yield pid, mode, veh

    @property
    def freq(self):
        """Return hh_freq, else if None, return the average frequency of household members.

        TODO: note this assumes we are basing hh freq on person freq.
        TODO: replace this with something better.
        """
        if self.hh_freq:
            return self.hh_freq

        if not self.people:
            self.logger.warning(f"Unknown hh weight for empty hh {self.hid}, returning None.")
            return None

        return self.av_person_freq

    def set_freq(self, freq):
        self.hh_freq = freq

    @property
    def av_person_freq(self):
        if not self.people:
            self.logger.warning(f"Unknown hh weight for empty hh {self.hid}, returning None.")
            return None
        frequencies = [person.freq for person in self.people.values()]
        if None in frequencies:
            self.logger.warning(f"Missing person weight in hh {self.hid}, returning None.")
            return None
        return sum(frequencies) / len(frequencies)

    def fix_plans(self, crop=True, times=True, locations=True):
        for _, person in self:
            if crop:
                person.plan.crop()
            if times:
                person.plan.fix_time_consistency()
            if locations:
                person.plan.fix_location_consistency()

    def shared_activities(self):
        shared_activities = []
        household_activities = []
        for pid, person in self.people.items():
            for activity_ in person.activities:
                if activity_.isin_exact(household_activities):
                    shared_activities.append(activity_)
                if not activity_.isin_exact(household_activities):
                    household_activities.append(activity_)
        return shared_activities

    def print(self):
        print(self)
        print(self.attributes)
        for _, person in self:
            person.print()

    def size(self):
        return len(self.people)

    def plot(self, **kwargs):
        plot.plot_household(self, **kwargs)

    def build_travel_geodataframe(self, **kwargs) -> gpd.GeoDataFrame:
        """Builds geopandas.GeoDataFrame for travel Legs found for persons within a Household.

        Keyword Args: Keyword arguments for plot.plans.build_person_travel_geodataframe
            from_epsg (str): coordinate system the plans are currently in
            to_epsg (str): coordinate system you want the geo dataframe to be projected to, optional, you need to specify from_epsg as well to use this.

        Returns:
            geopandas.GeoDataFrame:  with columns for household id (hid) and person id (pid).
        """
        gdf = None
        for _, person in self:
            _gdf = person.build_travel_geodataframe(**kwargs)
            _gdf["hid"] = self.hid
            if gdf is None:
                gdf = _gdf
            else:
                gdf = pd.concat([gdf, _gdf])
        gdf = gdf.sort_values(["pid", "seq"]).reset_index(drop=True)
        return gdf

    def plot_travel_plotly(self, epsg: str = "epsg:4326", **kwargs) -> None:
        """Uses plotly's Scattermapbox to plot persons' travel.

        Args:
            epsg (str): coordinate system the plans spatial information is in, e.g. 'epsg:27700'.

        Keyword Args: Keyword arguments for plot.plot_travel_plans
            gdf (geopandas.GeoDataFrame): generated by build_person_travel_geodataframe.
            groupby (list): optional argument for splitting traces in the plot.
            colour_by (str): argument for specifying what the colour should correspond to in the plot, travel mode by default.
            cmap (dict): optional argument, useful to pass if generating a number of plots and want to keep colour scheme consistent.
            mapbox_access_token (str): required to generate the plot (see https://docs.mapbox.com/help/how-mapbox-works/access-tokens/).

        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"), **kwargs
        )

    def __str__(self):
        return f"Household: {self.hid}"

    def __iadd__(self, other):
        """Unsafe addition with assignment (no guarantee of unique ids)."""
        self.logger.debug(
            "Note that this method requires all identifiers from populations being combined to be unique."
        )
        if isinstance(other, Household):
            for pid, person in other.people.items():
                self.people[pid] = copy.deepcopy(person)
            return self
        if isinstance(other, Person):
            self.people[other.pid] = copy.deepcopy(other)
            return self
        raise TypeError(
            f"Object for addition must be a Household or Person object, not {type(other)}"
        )

    def reindex(self, prefix: str):
        """Safely reindex all person identifiers in household using a prefix.

        Args:
            prefix (str): Prefix to add.
        """
        self.hid = prefix + self.hid
        for pid in list(self.people):
            person = self.people[pid]
            new_pid = prefix + pid
            if new_pid in self.people:
                raise KeyError(f"Duplicate person identifier (pid): {new_pid}")
            person.reindex(prefix)
            self.people[new_pid] = person
            del self.people[pid]

    def pickle(self, path):
        with open(path, "wb") as file:
            pickle.dump(self, file)


class Person:
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        pid,
        freq=None,
        attributes: dict = {},
        vehicles: Optional[dict[str, Vehicle]] = None,
        home_location: Optional[Location] = None,
        home_area=None,
        home_loc=None,
    ):
        self.pid = pid
        self.person_freq = freq
        self.attributes = attributes

        if vehicles is not None:
            self.vehicles = vehicles
        else:
            self.vehicles = {}

        if home_location is not None:
            self.home_location = home_location
        else:
            self.home_location = Location()

        if home_area:
            self.home_location.area = home_area
        if home_loc:
            self.home_location.loc = home_loc
        # person and their plan share Location
        self.plan = activity.Plan(home_location=self.home_location)
        self.plans_non_selected = []

    @property
    def freq(self):
        """Return person_freq, else if None, return the average frequency of legs.

        TODO consider passing parent hh on creation so that we can retrieve hh freq if required.
        """
        if self.person_freq:
            return self.person_freq
        return self.av_trip_freq

    def set_freq(self, freq):
        self.person_freq = freq

    @property
    def av_trip_freq(self):
        if not self.num_legs:
            return None
        frequencies = [leg.freq for leg in self.legs]
        if None in frequencies:
            return None
        return sum(frequencies) / len(frequencies)

    @property
    def av_activity_freq(self):
        frequencies = [act.freq for act in self.activities]
        if None in frequencies:
            return None
        return sum(frequencies) / len(frequencies)

    @property
    def home(self):
        if self.home_location.exists:
            return self.home_location
        if self.plan:
            return self.plan.home

    @property
    def subpopulation(self):
        return self.attributes.get("subpopulation")

    def set_location(self, location: Location):
        self.home_location = location
        self.plan.home_location = location

    def set_area(self, area):
        self.home_location.area = area
        self.plan.home_location.area = area

    def set_loc(self, loc):
        self.home_location.loc = loc
        self.plan.home_location.loc = loc

    def assign_vehicles_from_manager(self, manager: VehicleManager):
        """Assign vehicles to person from vehicles manager.
        This method removes the vehicles attribute from the agent and uses it to populate
        Person.vehicles variable. This method is used by read.matsim to transfer regular vehicles
        and electric vehicles from MATSim xml formats to each Person.

        Args:
            manager (VehicleManager): Population vehicles.
        """
        self.vehicles = {
            mode: manager.pop(vid) for mode, vid in self.attributes.pop("vehicles", {}).items()
        }

    @property
    def activities(self):
        if self.plan:
            for act in self.plan.activities:
                yield act

    @property
    def acts(self):
        if self.plan:
            for act in self.plan.activities:
                yield act

    @property
    def num_activities(self):
        if self.plan:
            return len(list(self.activities))
        return 0

    @property
    def legs(self):
        if self.plan:
            for leg in self.plan.legs:
                yield leg

    @property
    def num_legs(self):
        if self.plan:
            return len(list(self.legs))
        return 0

    def iter_vehicles(self):
        for mode, veh in self.vehicles.items():
            yield mode, veh

    def evs(self):
        for mode, veh in self.vehicles.items():
            if isinstance(veh, ElectricVehicle):
                yield mode, veh

    @property
    def length(self):
        return len(self.plan)

    def __len__(self):
        return self.length

    def __getitem__(self, val):
        return self.plan[val]

    @property
    def last_component(self):
        if self.plan:
            return self.plan[-1]
        return None

    @property
    def last_activity(self):
        acts = list(self.activities)
        if acts:
            return acts[-1]
        return None

    @property
    def last_leg(self):
        legs = list(self.legs)
        if legs:
            return legs[-1]
        return None

    def __iter__(self):
        for component in self.plan:
            yield component

    def __eq__(self, other):
        """Check for equality of two persons, equality is based on equal attributes and activity plans."""
        if not isinstance(other, Person):
            self.logger.warning(f"Cannot compare person to non person: ({type(other)})")
            return False
        if not self.attributes == other.attributes:
            return False
        if not self.plan == other.plan:
            return False
        if not len(self.plans_non_selected) == len(other.plans_non_selected):
            return False
        for plana, planb in zip(self.plans_non_selected, other.plans_non_selected):
            if not plana == planb:
                return False
        return True

    @property
    def activity_classes(self):
        return self.plan.activity_classes

    @property
    def mode_classes(self):
        return self.plan.mode_classes

    @property
    def has_valid_plan(self) -> bool:
        """Check sequence of Activities and Legs.

        Returns:
            bool:
        """
        return self.plan.is_valid

    def validate(self):
        """Validate plan."""
        self.plan.validate()
        return True

    def validate_sequence(self) -> True:
        """Check sequence of Activities and Legs.

        Returns:
            True:
        """
        if not self.plan.valid_sequence:
            raise PAMSequenceValidationError(f"Person {self.pid} has invalid plan sequence")

        return True

    def validate_times(self) -> True:
        """Check sequence of Activity and Leg times.

        Returns:
            True:
        """
        if not self.plan.valid_time_sequence:
            raise PAMInvalidTimeSequenceError(f"Person {self.pid} has invalid plan times")

        return True

    def validate_locations(self) -> True:
        """Check sequence of Activity and Leg locations.

        Returns:
            True:
        """
        if not self.plan.valid_locations:
            raise PAMValidationLocationsError(f"Person {self.pid} has invalid plan locations")

        return True

    @property
    def closed_plan(self) -> bool:
        """Check if plan starts and stops at the same facility (based on activity and location).

        Returns:
            bool:
        """
        return self.plan.closed

    @property
    def first_activity(self):
        return self.plan.first

    @property
    def home_based(self):
        return self.plan.home_based

    def add(self, p: Any) -> None:
        """Safely add a new component to the plan.

        Args:
            p (Any): component to add.
        """
        self.plan.add(p)

    def finalise(self):
        """Add activity end times based on start time of next activity."""
        self.plan.finalise_activity_end_times()

    def fix_plan(self, crop=True, times=True, locations=True):
        if crop:
            self.plan.crop()
        if times:
            self.plan.fix_time_consistency()
        if locations:
            self.plan.fix_location_consistency()

    def clear_plan(self):
        self.plan.clear()

    def print(self):
        print(self)
        print(self.attributes)
        self.plan.print()

    def plot(self, **kwargs):
        plot.plot_person(self, **kwargs)

    def reindex(self, prefix: str):
        self.pid = prefix + self.pid

    def build_travel_geodataframe(self, **kwargs) -> gpd.GeoDataFrame:
        """Builds geopandas.GeoDataFrame for Person's Legs.

        Keyword Args: Keyword arguments for plot.build_person_travel_geodataframe,
            from_epsg (str): coordinate system the plans are currently in
            to_epsg (str): coordinate system you want the geo dataframe to be projected to, optional, you need to specify from_epsg as well to use this.

        Returns:
            geopandas.GeoDataFrame: columns for person id (pid).
        """
        return plot.build_person_travel_geodataframe(self, **kwargs)

    def plot_travel_plotly(self, epsg: str = "epsg:4326", **kwargs) -> go.Figure:
        """Uses plotly's Scattermapbox to plot persons' travel.

        Args:
            epsg (str, optional): coordinate system the plans spatial information is in, e.g. 'epsg:27700'. Defaults to "epsg:4326".

        Keyword Args: Keyword arguments for plot.plot_travel_plans
            gdf (geopandas.GeoDataFrame): generated by build_person_travel_geodataframe.
            groupby (list): optional argument for splitting traces in the plot.
            colour_by (str): argument for specifying what the colour should correspond to in the plot, travel mode by default.
            cmap (dict): optional argument, useful to pass if generating a number of plots and want to keep colour scheme consistent.
            mapbox_access_token (str): required to generate the plot (see https://docs.mapbox.com/help/how-mapbox-works/access-tokens/).

        Returns:
            go.Figure: Plotly figure object
        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"), **kwargs
        )

    def __str__(self):
        return f"Person: {self.pid}"

    def remove_activity(self, seq: int) -> tuple:
        """Remove an activity from plan at given seq. Check for wrapped removal.

        Args:
            seq (int):
        Returns:
            tuple: (adjusted) idx of previous and subsequent activities as a tuple
        """
        return self.plan.remove_activity(seq)

    def move_activity(self, seq: Any, default: str = "home", new_mode: str = "walk") -> None:
        """Move an activity from plan at given seq to default location.

        Args:
            seq (Any):
            default (str, optional):
                'home' or pam.activity.Location.
                Defaults to "home".
            new_mode (str, optional):
                access/egress journey switching to this mode. Ie 'walk'.
                Defaults to "walk".
        """
        return self.plan.move_activity(seq, default, new_mode)

    def fill_plan(self, p_idx: Any, s_idx: Any, default: str = "home") -> bool:
        """Fill a plan after Activity has been removed.

        Args:
            p_idx (Any): location of previous Activity
            s_idx (Any): location of subsequent Activity
            default (str, optional): Defaults to "home"
        Returns:
            bool:
        """
        return self.plan.fill_plan(p_idx, s_idx, default=default)

    def stay_at_home(self):
        self.plan.stay_at_home()

    def pickle(self, path):
        with open(path, "wb") as file:
            pickle.dump(self, file)
