import logging
import random
import pickle
import copy
from collections import defaultdict
from typing import Optional
import pandas as pd

from pam.location import Location
import pam.activity as activity
import pam.plot as plot
from pam import write
from pam import PAMSequenceValidationError, PAMTimesValidationError, PAMValidationLocationsError, PAMVehicleIdError
from pam import variables
from pam.vehicle import Vehicle, ElectricVehicle


class Population:

    def __init__(self, name: str = None):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.households = {}

    def add(self, household):
        if not isinstance(household, Household):
            raise UserWarning(f"Expected instance of Household, not: {type(household)}")
        self.households[household.hid] = household

    def get(self, hid, default=None):
        return self.households.get(hid, default)

    def __getitem__(self, hid):
        return self.households[hid]

    def __iter__(self):
        for hid, household in self.households.items():
            yield hid, household

    def people(self):
        """
        Iterator for people in poulation, returns hid, pid and Person
        """
        for hid, household in self.households.items():
            for pid, person in household.people.items():
                yield hid, pid, person

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
        raise UserWarning(f"Cannot check if population contains object type: {type(other)}, please provide a Household or Person.")

    def __eq__(self, other):
        """
        Check for equality of two populations, equality is based on equal attributes and activity plans
        of all household and household members. Identifiers (eg hid and pid) are disregarded.
        """
        if not isinstance(other, Population):
            self.logger.warning(f"Cannot compare population to non population: ({type(other)}), please provide a Population.")
            return False
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
    def attributes(self, show:int = 10) -> dict:
        attributes = defaultdict(set)
        for _, hh in self.households.items():

            for k, v in hh.attributes.items():
                attributes[k].add(v)
            for _, p in hh.people.items():
                for k, v in p.attributes.items():
                    attributes[k].add(v)
        for k, v in attributes.items():
            if len(v) > show:
                attributes[k] = set(list(attributes[k])[:show])
        return dict(attributes)

    @property
    def has_vehicles(self):
        return bool(list(self.vehicles()))

    @property
    def has_electric_vehicles(self):
        return bool(list(self.electric_vehicles()))

    @property
    def has_uniquely_indexed_vehicle_types(self):
        # checks indexing of vehicle types in population
        vehicle_types = self.vehicle_types()
        all_vehicle_type_ids = [vt.id for vt in vehicle_types]
        unique_vehicle_type_ids = set(all_vehicle_type_ids)
        return len(all_vehicle_type_ids) == len(unique_vehicle_type_ids)

    def vehicles(self):
        for _, _, p in self.people():
            v = p.vehicle
            if v is not None:
                yield v

    def electric_vehicles(self):
        for v in self.vehicles():
            if isinstance(v, ElectricVehicle):
                yield v

    def vehicle_types(self):
        v_types = {p.vehicle.vehicle_type for _, _, p in self.people() if p.vehicle is not None}
        for vt in v_types:
            yield vt

    def electric_vehicle_charger_types(self):
        chargers = set()
        for v in self.electric_vehicles():
            chargers |= set(v.charger_types.split(','))
        return chargers

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
            'num_households': num_households,
            'num_people': num_people,
            'num_activities': num_activities,
            'num_legs': num_legs,
        }

    def legs_df(self) -> pd.DataFrame:
        """
        Extract tabular record of population legs.
        :return pd.DataFrame: record of legs
        """
        df = []
        for hid, pid, person in self.people():
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
        self.add_fields(df)
        return df


    def trips_df(self) -> pd.DataFrame:
        """
        Extract tabular record of population legs.
        :return pd.DataFrame: record of legs
        """
        df = []
        for hid, pid, person in self.people():
            for seq, trip in enumerate(person.plan.trips()):
                record = {
                        'pid': pid,
                        'hid': hid,
                        'hzone': person.home,
                        'ozone': trip.start_location.area,
                        'dzone': trip.end_location.area,
                        'oloc': trip.start_location,
                        'dloc': trip.end_location,
                        'seq': seq,
                        'purp': trip.purp,
                        'mode': trip.mode,
                        'tst': trip.start_time.time(),
                        'tet': trip.end_time.time(),
                        'duration': trip.duration / pd.Timedelta(minutes = 1), #duration in minutes
                        'euclidean_distance': trip.euclidean_distance,
                        'freq': person.freq,
                    }
                record = {**record, **dict(person.attributes)} # add person attributes
                df.append(record)

        df = pd.DataFrame(df)
        self.add_fields(df)
        return df

    @staticmethod
    def add_fields(df):
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

    def build_travel_geodataframe(self, **kwargs):
        """
        Builds geopandas.GeoDataFrame for travel Legs found for all agents in the Population.
        :param kwargs: arguments for plot.build_person_travel_geodataframe,
            from_epsg: coordinate system the plans are currently in
            to_epsg: coordinate system you want the geo dataframe to be projected to, optional, you need to specify
                from_epsg as well to use this.
        :return: geopandas.GeoDataFrame with columns for household id (hid) and person id (pid)
        """
        gdf = None
        for hid, household in self.households.items():
            _gdf = household.build_travel_geodataframe(**kwargs)
            if gdf is None:
                gdf = _gdf
            else:
                gdf = gdf.append(_gdf)
        gdf = gdf.sort_values(['hid', 'pid', 'seq']).reset_index(drop=True)
        return gdf

    def plot_travel_plotly(self, epsg: str = 'epsg:4326', **kwargs):
        """
        Uses plotly's Scattermapbox to plot agents' travel
        :param epsg: coordinate system the plans spatial information is in, e.g. 'epsg:27700'
        :param kwargs: arguments for plot.plot_travel_plans
            :param gdf: geopandas.GeoDataFrame generated by build_person_travel_geodataframe
            :param groupby: optional argument for splitting traces in the plot
            :param colour_by: argument for specifying what the colour should correspond to in the plot, travel mode by
            default
            :param cmap: optional argument, useful to pass if generating a number of plots and want to keep colour
            scheme
            consistent
            :param mapbox_access_token: required to generate the plot
            https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
        :return:
        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"),
            **kwargs
        )

    def fix_plans(
        self,
        crop: bool = True,
        times = True,
        locations = True
        ):
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
        with open(path, 'wb') as file:
            pickle.dump(self, file)

    def to_csv(
        self,
        dir: str,
        crs = None,
        to_crs: str = "EPSG:4326"
        ):
        write.to_csv(self, dir, crs, to_crs)

    def __str__(self):
        return f"Population: {self.population} people in {self.num_households} households."

    def __iadd__(self, other):
        """
        Unsafe addition with assignment (no guarantee of unique ids).
        """
        self.logger.debug("Note that this method requires all identifiers from populations being combined to be unique.")
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
        raise TypeError(f"Object for addition must be a Population Household or Person object, not {type(other)}")

    def reindex(self, prefix: str):
        """
        Safely reindex all household and person identifiers in population using a prefix.
        """
        for hid in list(self.households):
            hh = self.households[hid]
            new_hid = prefix + str(hid)
            if new_hid in self.households:
                raise KeyError(f"Duplicate household identifier (hid): {new_hid}")

            hh.reindex(prefix)

            self.households[new_hid] = hh
            del self.households[hid]

    def combine(self, other, prefix=""):
        """
        Safe addition with assignment by adding a prefix to create unique pids and hids.
        """
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
            hh = Household(other.pid) # we create a new hh for single person
            hh.add(other)
            hh.reindex(prefix)
            self += hh
            return None
        raise TypeError(f"Object for addition must be a Population Household or Person object, not {type(other)}")


    def sample_locs(self, sampler, long_term_activities = None, joint_trips_prefix = 'escort_'):
        """
        WIP Sample household plan locs using a sampler.

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

        TODO - add method to all core classes
        :params list long_term activities: a list of activities for which location is only assigned once (per zone)
        :params str joint_trips_prefix: a purpose prefix used to identify escort/joint trips
        """
        if long_term_activities is None:
            long_term_activities = variables.LONG_TERM_ACTIVITIES

        for _, household in self.households.items():

            home_loc = activity.Location(
                area=household.location.area,
                loc=sampler.sample(household.location.area, 'home')
            )

            unique_locations = {(household.location.area, 'home'): home_loc}

            for __, person in household.people.items():

                for act in person.activities:

                    # remove escort prefix from activity types.
                    if act.act[:len(joint_trips_prefix)] == joint_trips_prefix:
                        target_act = act.act[(len(joint_trips_prefix)):]
                    else:
                        target_act = act.act

                    if (act.location.area, target_act) in unique_locations:
                        location = unique_locations[(act.location.area, target_act)]
                        act.location = location

                    else:
                        location = activity.Location(
                            area=act.location.area,
                            loc=sampler.sample(act.location.area, target_act)
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
                        component.start_location = person.plan[idx-1].location
                        component.end_location = person.plan[idx+1].location


    def sample_locs_complex(self, sampler, long_term_activities = None, joint_trips_prefix = 'escort_'):
        """
        Extends sample_locs method to enable more complex and rules-based sampling.
        Keeps track of the last location and transport mode, to apply distance- and mode-based sampling rules.
        It is generally slower than sample_locs, as it loops through both activities and legs.
        :params list long_term activities: a list of activities for which location is only assigned once (per zone)
        :params str joint_trips_prefix: a purpose prefix used to identify escort/joint trips
        """
        if long_term_activities is None:
            long_term_activities = variables.LONG_TERM_ACTIVITIES


        for _, household in self.households.items():
            home_loc = activity.Location(
                area=household.location.area,
                loc=sampler.sample(household.location.area, 'home', mode = None, previous_duration=None, previous_loc = None)
            )
            mode = None

            unique_locations = {(household.location.area, 'home'): home_loc}

            for _, person in household.people.items():
                mode = None
                previous_duration = None
                previous_loc = None

                for idx, component in enumerate(person.plan):
                    # loop through all plan elements

                    if isinstance(component, activity.Leg):
                        mode = component.mode # keep track of last mode
                        previous_duration = component.duration

                    elif isinstance(component, activity.Activity):
                        act = component

                        # remove "escort_" from activity types.
                        # TODO: model joint trips
                        if act.act[:len(joint_trips_prefix)] == joint_trips_prefix:
                            target_act = act.act[(len(joint_trips_prefix)):]
                        else:
                            target_act = act.act

                        if (act.location.area, target_act) in unique_locations:
                            location = unique_locations[(act.location.area, target_act)]
                            act.location = location

                        else:
                            location = activity.Location(
                                area=act.location.area,
                                loc=sampler.sample(act.location.area, target_act, mode = mode, previous_duration = previous_duration, previous_loc = previous_loc)
                            )
                            if target_act in long_term_activities:
                                unique_locations[(act.location.area, target_act)] = location
                            act.location = location

                        previous_loc = location.loc # keep track of previous location

                # complete the alotting activity locations to the trip starts and ends.
                for idx in range(person.plan.length):
                    component = person.plan[idx]
                    if isinstance(component, activity.Leg):
                        component.start_location = person.plan[idx-1].location
                        component.end_location = person.plan[idx+1].location



class Household:
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        hid,
        attributes={},
        freq=None,
        location: Optional[Location] = None,
        area=None,
        loc=None
        ):
        self.hid = hid
        self.people = {}
        self.attributes = attributes
        self.hh_freq=freq
        if location:
            self._location = location
        else:
            self._location = Location()
        if area:  # potential overwrite
            self._location.area = area
        if loc:  # potential overwrite
            self._location.loc = loc

    def add(self, person):
        if not isinstance(person, Person):
            raise UserWarning(f"Expected instance of Person, not: {type(person)}")
        # person.finalise()
        self.people[person.pid] = person

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
            raise UserWarning(f"Cannot check if household contains object type: {type(other_person)}, please provide Person.")
        for _, person in self:
            if other_person == person:
                return True
        return False

    def __eq__(self, other):
        """
        Check for equality of two households, equality is based on equal attributes and activity plans
        of household and household members. Identifiers (eg hid and pid) are disregarded unless they
        are included in attributes.
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

    def set_location(self, location:Location):
        """
        Set both hh and person home_location, but note that hhs and
        their persons do not share location object.
        """
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
        return set(l.mode for l in self.legs)

    def get_attribute(self, key) -> set:
        """
        Get set of attribute values for given key, First searches hh attributes then occupants.
        """
        if key in self.attributes:
            return {self.attributes[key]}
        attributes = set()
        for _, person in self:
            attributes.add(person.attributes.get(key))
        return attributes

    @property
    def subpopulation(self):
        return self.get_attribute("subpopulation")

    @property
    def freq(self):
        """
        Return hh_freq, else if None, return the average frequency of household members.
        # TODO note this assumes we are basing hh freq on person freq.
        # TODO replace this with something better.
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
            for activity in person.activities:
                if activity.isin_exact(household_activities):
                    shared_activities.append(activity)
                if not activity.isin_exact(household_activities):
                    household_activities.append(activity)
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

    def build_travel_geodataframe(self, **kwargs):
        """
        Builds geopandas.GeoDataFrame for travel Legs found for agents within a Household
        :param kwargs: arguments for plot.build_person_travel_geodataframe,
            from_epsg: coordinate system the plans are currently in
            to_epsg: coordinate system you want the geo dataframe to be projected to, optional, you need to specify
                from_epsg as well to use this.
        :return: geopandas.GeoDataFrame with columns for household id (hid) and person id (pid)
        """
        gdf = None
        for _, person in self:
            _gdf = person.build_travel_geodataframe(**kwargs)
            _gdf['hid'] = self.hid
            if gdf is None:
                gdf = _gdf
            else:
                gdf = gdf.append(_gdf)
        gdf = gdf.sort_values(['pid', 'seq']).reset_index(drop=True)
        return gdf

    def plot_travel_plotly(self, epsg='epsg:4326', **kwargs):
        """
        Uses plotly's Scattermapbox to plot agents' travel
        :param epsg: coordinate system the plans spatial information is in, e.g. 'epsg:27700'
        :param kwargs: arguments for plot.plot_travel_plans
            :param gdf: geopandas.GeoDataFrame generated by build_person_travel_geodataframe
            :param groupby: optional argument for splitting traces in the plot
            :param colour_by: argument for specifying what the colour should correspond to in the plot, travel mode by
            default
            :param cmap: optional argument, useful to pass if generating a number of plots and want to keep colour
            scheme
            consistent
            :param mapbox_access_token: required to generate the plot
            https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
        :return:
        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"),
            **kwargs
        )

    def __str__(self):
        return f"Household: {self.hid}"

    def __iadd__(self, other):
        """
        Unsafe addition with assignment (no guarantee of unique ids).
        """
        self.logger.debug("Note that this method requires all identifiers from populations being combined to be unique.")
        if isinstance(other, Household):
            for pid, person in other.people.items():
                self.people[pid] = copy.deepcopy(person)
            return self
        if isinstance(other, Person):
            self.people[other.pid] = copy.deepcopy(other)
            return self
        raise TypeError(f"Object for addition must be a Household or Person object, not {type(other)}")

    def reindex(self, prefix: str):
        """
        Safely reindex all person identifiers in household using a prefix.
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
        with open(path, 'wb') as file:
            pickle.dump(self, file)


class Person:
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        pid,
        freq=None,
        attributes={},
        home_location: Optional[Location] = None,
        home_area=None,
        home_loc=None,
        vehicle: Vehicle = None
        ):
        self.pid = pid
        self.person_freq = freq
        self.attributes = attributes
        if home_location is not None:
            self.home_location = home_location
        else:
            self.home_location = Location()
        if home_area:
            self.home_location.area = home_area
        if home_loc:
            self.home_location.loc = home_loc
        self.plan = activity.Plan(home_location=self.home_location)  # person and their plan share Location
        self.plans_non_selected = []
        self.vehicle = None
        if vehicle:
            self.assign_vehicle(vehicle)

    @property
    def freq(self):
        """
        Return person_freq, else if None, return the average frequency of legs.
        TODO consider passing parent hh on creation so that we can retrieve hh freq if required.
        """
        if self.person_freq:
            return self.person_freq
        return self.av_trip_freq

    def set_freq(self, freq):
        self.person_freq = freq

    def assign_vehicle(self, vehicle: Vehicle):
        """
        Give a Vehicle or ElectricVehicle to an agent
        :param vehicle:
        :return:
        """
        if vehicle.id != self.pid:
            raise PAMVehicleIdError(f'Vehicle with ID: {vehicle.id} does not match Person ID: {self.pid}')
        self.vehicle = vehicle

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

    def set_location(self, location:Location):
        self.home_location = location
        self.plan.home_location = location

    def set_area(self, area):
        self.home_location.area = area
        self.plan.home_location.area = area

    def set_loc(self, loc):
        self.home_location.loc = loc
        self.plan.home_location.loc = loc

    @property
    def activities(self):
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
        """
        Check for equality of two persons, equality is based on equal attributes and activity plans.
        """
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
    def has_valid_plan(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        return self.plan.is_valid

    def validate(self):
        """
        Validate plan.
        """
        self.plan.validate()
        return True

    def validate_sequence(self):
        """
        Check sequence of Activities and Legs.
        :return: True
        """
        if not self.plan.valid_sequence:
            raise PAMSequenceValidationError(f"Person {self.pid} has invalid plan sequence")

        return True

    def validate_times(self):
        """
        Check sequence of Activity and Leg times.
        :return: True
        """
        if not self.plan.valid_times:
            raise PAMTimesValidationError(f"Person {self.pid} has invalid plan times")

        return True

    def validate_locations(self):
        """
        Check sequence of Activity and Leg locations.
        :return: True
        """
        if not self.plan.valid_locations:
            raise PAMValidationLocationsError(f"Person {self.pid} has invalid plan locations")

        return True

    @property
    def closed_plan(self):
        """
        Check if plan starts and stops at the same facility (based on activity and location)
        :return: Bool
        """
        return self.plan.closed

    @property
    def first_activity(self):
        return self.plan.first

    @property
    def home_based(self):
        return self.plan.home_based

    def add(self, p):
        """
        Safely add a new component to the plan.
        :param p:
        :return:
        """
        self.plan.add(p)

    def finalise(self):
        """
        Add activity end times based on start time of next activity.
        """
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

    def build_travel_geodataframe(self, **kwargs):
        """
        Builds geopandas.GeoDataFrame for Person's Legs
        :param kwargs: arguments for plot.build_person_travel_geodataframe,
            from_epsg: coordinate system the plans are currently in
            to_epsg: coordinate system you want the geo dataframe to be projected to, optional, you need to specify
                from_epsg as well to use this.
        :return: geopandas.GeoDataFrame with columns for person id (pid)
        """
        return plot.build_person_travel_geodataframe(self, **kwargs)

    def plot_travel_plotly(self, epsg='epsg:4326', **kwargs):
        """
        Uses plotly's Scattermapbox to plot agents' travel
        :param epsg: coordinate system the plans spatial information is in, e.g. 'epsg:27700'
        :param kwargs: arguments for plot.plot_travel_plans
            :param gdf: geopandas.GeoDataFrame generated by build_person_travel_geodataframe
            :param groupby: optional argument for splitting traces in the plot
            :param colour_by: argument for specifying what the colour should correspond to in the plot, travel mode by
            default
            :param cmap: optional argument, useful to pass if generating a number of plots and want to keep colour
            scheme
            consistent
            :param mapbox_access_token: required to generate the plot
            https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
        :return:
        """
        return plot.plot_travel_plans(
            gdf=self.build_travel_geodataframe(from_epsg=epsg, to_epsg="epsg:4326"),
            **kwargs
        )

    def __str__(self):
        return f"Person: {self.pid}"

    def remove_activity(self, seq):
        """
        Remove an activity from plan at given seq.
        Check for wrapped removal.
        Return (adjusted) idx of previous and subsequent activities as a tuple
        :param seq:
        :return: tuple
        """
        return self.plan.remove_activity(seq)

    def move_activity(self, seq, default='home', new_mode='walk'):
        """
        Move an activity from plan at given seq to default location
        :param seq:
        :param default: 'home' or pam.activity.Location
        :param new_mode: access/egress journey switching to this mode. Ie 'walk'
        :return: None
        """
        return self.plan.move_activity(seq, default, new_mode)

    def fill_plan(self, p_idx, s_idx, default='home'):
        """
        Fill a plan after Activity has been removed.
        :param p_idx: location of previous Activity
        :param s_idx: location of subsequent Activity
        :param default:
        :return: bool
        """
        return self.plan.fill_plan(p_idx, s_idx, default=default)

    def stay_at_home(self):
        self.plan.stay_at_home()

    def pickle(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)
