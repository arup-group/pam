import logging
import os
import pickle
import random
from collections.abc import Generator, Iterator
from typing import Any, Optional

import geopandas as gp
import numpy as np
import pandas as pd
import shapely
from lxml import etree as et

from pam import variables
from pam.samplers.spatial import RandomPointSampler
from pam.utils import DEFAULT_GZIP_COMPRESSION, create_crs_attribute, create_local_dir, is_gzip


class FacilitySampler:
    def __init__(
        self,
        facilities: gp.GeoDataFrame,
        zones: gp.GeoDataFrame,
        activities: Optional[list] = None,
        build_xml: bool = True,
        fail: bool = True,
        random_default: bool = True,
        weight_on: Optional[str] = None,
        max_walk: Optional[float] = None,
        transit_modes: Optional[list] = None,
        expected_euclidean_speeds: Optional[dict] = None,
        activity_areas_path: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> None:
        """Sampler object for facilities.

        Note:
          If a zone id is missing then the sampler will not be able to default to random sample, so will either return None or fail as per the fail flag.

        Args:
            facilities (gp.GeoDataFrame): facilities Geodataframe
            zones (gp.GeoDataFrame): zones Geodataframe
            activities (Optional[list], optional): optionally set list of subset of activities to be considered. Defaults to None.
            build_xml (bool, optional): flag to build a facility xml output (for MATSim). Defaults to True.
            fail (bool, optional): flag hard fail if sample not found. Defaults to True.
            random_default (bool, optional): flag for defaulting to random sample when activity missing. Defaults to True.
            weight_on (Optional[str], optional): the column name of the facilities geodataframe which contains facility weights (for sampling). Defaults to None.
            max_walk (Optional[float], optional): maximum walking distnace from a transit stop. Defaults to None.
            transit_modes (Optional[list], optional):  a list of PT modes. If not specified, the default list in variables.TRANSIT_MODES is used. Defaults to None.
            expected_euclidean_speeds (Optional[dict], optional): a dictionary specifying the euclidean speed of the various modes (m/s). If not specified, the default list in variables.EXPECTED_EUCLIDEAN_SPEEDS is used. Defaults to None.
            activity_areas_path (Optional[str], optional): path to the activity areas shapefile (previously exported throught the FacilitySampler.export_activity_areas method). Defaults to None.
            seed (Optional[int], optional): If given, seed number for reproducible results. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)

        # Fix random seed
        self.seed = seed

        if activities is None:
            self.activities = list(set(facilities.activity))
        else:
            self.activities = activities

        ## overrides for transit mode and speed specifications
        self.TRANSIT_MODES = transit_modes if transit_modes is not None else variables.TRANSIT_MODES
        self.EXPECTED_EUCLIDEAN_SPEEDS = (
            expected_euclidean_speeds
            if expected_euclidean_speeds is not None
            else variables.EXPECTED_EUCLIDEAN_SPEEDS
        )

        # spatial join
        if activity_areas_path is None:
            self.activity_areas = self.spatial_join(facilities, zones)
            self.activity_areas_dict = self.activity_areas_indexing(self.activity_areas)
        else:
            self.load_activity_areas(activity_areas_path)

        # build samplers
        self.samplers = self.build_facilities_sampler(
            self.activity_areas_dict, weight_on=weight_on, max_walk=max_walk
        )
        self.build_xml = build_xml
        self.fail = fail
        self.random_default = random_default

        if random_default:
            self.random_sampler = RandomPointSampler(geoms=zones, fail=fail, seed=seed)

        self.facilities = {}
        self.index_counter = 0
        self.error_counter = 0

    def clear(self):
        self.facilities = {}

    def sample(
        self,
        location_idx: str,
        activity: str,
        mode: Optional[str] = None,
        previous_duration: Optional[pd.Timedelta] = None,
        previous_loc: Optional[shapely.geometry.Point] = None,
    ) -> shapely.geometry.Point:
        """Sample a Point from the given location and for the given activity.

        Args:
            location_idx (str): the zone to sample from
            activity (str): activity purpose
            mode (Optional[str], optional): transport mode used to access facility. Defaults to None.
            previous_duration (Optional[pd.Timedelta], optional): the time duration of the arriving leg. Defaults to None.
            previous_loc (Optional[shapely.geometry.Point], optional): the location of the last visited activity. Defaults to None.

        Returns:
            shapely.geometry.Point: Sampled point
        """
        idx, loc = self.sample_facility(
            location_idx,
            activity,
            mode=mode,
            previous_duration=previous_duration,
            previous_loc=previous_loc,
        )

        if idx is not None and self.build_xml:
            self.facilities[idx] = {"loc": loc, "act": activity}

        return loc

    def sample_facility(
        self,
        location_idx: str,
        activity: str,
        patience=1000,
        mode: Optional[str] = None,
        previous_duration: Optional[pd.Timedelta] = None,
        previous_loc: Optional[shapely.geometry.Point] = None,
    ):
        """Sample a facility id and location. If a location idx is missing, can return a random location."""
        if location_idx not in self.samplers:
            if self.random_default:
                self.logger.warning(f"Using random sample for zone:{location_idx}:{activity}")
                idx = f"_{self.index_counter}"
                self.index_counter += 1
                return idx, self.random_sampler.sample(location_idx, activity)
            if self.fail:
                raise IndexError(f"Cannot find idx: {location_idx} in facilities sampler")
            self.logger.warning(f"Missing location idx:{location_idx}")
            return None, None

        sampler = self.samplers[location_idx][activity]

        if sampler is None:
            self.error_counter += 1
            if self.error_counter >= patience:
                raise UserWarning(f"Failures to sample, exceeded patience of {patience}.")
            if self.random_default:
                self.logger.warning(f"Using random sample for zone:{location_idx}:{activity}")
                idx = f"_{self.index_counter}"
                self.index_counter += 1
                return idx, self.random_sampler.sample(location_idx, activity)
            elif self.fail:
                raise UserWarning(
                    f"Cannot find activity: {activity} in location: {location_idx}, consider allowing random default."
                )
            else:
                return None, None
        else:
            self.error_counter = 0
            if isinstance(sampler, Generator):
                return next(sampler)
            else:
                return next(sampler(mode, previous_duration, previous_loc))

    def spatial_join(self, facilities, zones):
        "Spatially join facility and zone data."
        self.logger.warning("Joining facilities data to zones, this may take a while.")
        activity_areas = gp.sjoin(facilities, zones, how="inner", predicate="intersects")
        return activity_areas

    def activity_areas_indexing(self, activity_areas):
        """Convert joined zone-activities gdf to a nested dictionary for faster indexing.

        The first index level refers to zones, while the second to activity purposes.
        """
        activity_areas_dict = {x: {} for x in activity_areas["index_right"].unique()}
        for (zone, act), facility_data in activity_areas.groupby(["index_right", "activity"]):
            activity_areas_dict[zone][act] = facility_data

        return activity_areas_dict

    def export_activity_areas(self, filepath):
        "Export the spatially joined facilities-zones geodataframe."
        with open(filepath, "wb") as f:
            pickle.dump(self.activity_areas_dict, f)

    def load_activity_areas(self, filepath):
        "Load the spatially joined facilities-zones geodataframe."
        with open(filepath, "rb") as f:
            self.activity_areas_dict = pickle.load(f)

    def build_facilities_sampler(
        self,
        activity_areas: dict,
        weight_on: Optional[str] = None,
        max_walk: Optional[float] = None,
    ) -> dict:
        """Build facility location sampler from osmfs input.

        The sampler returns a tuple of (uid, Point).
        TODO: I do not like having a sjoin and assuming index names here
        TODO: look to move to more carefully defined input data format for facilities.

        Args:
            activity_areas (dict):
            weight_on (Optional[str], optional): a column (name) of the facilities geodataframe to be used as a sampling weight. Defaults to None.
            max_walk (Optional[float], optional): Defaults to None.

        Returns:
            dict:
        """
        sampler_dict = {}

        self.logger.warning("Building sampler, this may take a while.")
        for zone in set(activity_areas.keys()):
            sampler_dict[zone] = {}
            zone_facs = activity_areas.get(zone, {})

            for act in self.activities:
                self.logger.debug(f"Building sampler for zone:{zone} act:{act}.")
                facs = zone_facs.get(act, None)
                if facs is not None:
                    points = list(facs.geometry.items())
                    if weight_on is not None:
                        # weighted sampler
                        weights = facs[weight_on]
                        transit_distance = facs["transit"] if max_walk is not None else None
                        sampler_dict[zone][act] = inf_yielder(
                            points,
                            weights,
                            transit_distance,
                            max_walk,
                            self.TRANSIT_MODES,
                            self.EXPECTED_EUCLIDEAN_SPEEDS,
                            seed=self.seed,
                        )
                    else:
                        # simple sampler
                        sampler_dict[zone][act] = inf_yielder(points, seed=self.seed)
                else:
                    sampler_dict[zone][act] = None
        return sampler_dict

    def write_facilities_xml(self, path, comment=None, coordinate_reference_system=None):
        create_local_dir(os.path.dirname(path))

        compression = DEFAULT_GZIP_COMPRESSION if is_gzip(path) else 0
        with et.xmlfile(path, encoding="utf-8", compression=compression) as xf:
            xf.write_declaration()
            xf.write_doctype(
                '<!DOCTYPE facilities SYSTEM "http://matsim.org/files/dtd/facilities_v1.dtd">'
            )

            with xf.element("facilities"):
                if comment:
                    xf.write(et.Comment(comment), pretty_print=True)

                if coordinate_reference_system is not None:
                    xf.write(create_crs_attribute(coordinate_reference_system), pretty_print=True)

                for i, data in self.facilities.items():
                    facility_xml = et.Element(
                        "facility", {"id": str(i), "x": str(data["loc"].x), "y": str(data["loc"].y)}
                    )
                    et.SubElement(facility_xml, "activity", {"type": data["act"]})
                    xf.write(facility_xml, pretty_print=True)


def euclidean_distance(p1, p2):
    """Calculate euclidean distance between two Activity.location.loc objects."""
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


def inf_yielder(
    candidates: list[tuple[Any, shapely.geometry.Point]],
    weights: Optional[pd.Series] = None,
    transit_distance: Optional[pd.Series] = None,
    max_walk: Optional[float] = None,
    transit_modes: Optional[list[str]] = None,
    expected_euclidean_speeds: Optional[dict] = None,
    seed: Optional[int] = None,
) -> tuple[Any, shapely.geometry.Point]:
    """Redirect to the appropriate sampler.

    Args:
        candidates (list[tuple[Any, shapely.geometry.Point]]): Tuples contain candidate facilities index values and their geolocation.
        weights (Optional[pd.Series], optional): sampling weights (ie facility floorspace). Defaults to None.
        transit_distance (Optional[pd.Series], optional):  distance of each candidate facility from the closest PT stop. Defaults to None.
        max_walk (Optional[float], optional): maximum walking distance from a PT stop. Defaults to None.
        transit_modes (Optional[list[str]], optional): Possible transit modes. Defaults to None.
        expected_euclidean_speeds (Optional[dict], optional): Defaults to None.
        seed (Optional[int], optional): If given, seed number for reproducible results. Defaults to None.

    Returns:
        tuple[Any, shapely.geometry.Point]: Sampled candidate.
    """

    if isinstance(weights, pd.Series):
        return lambda mode=None, previous_duration=None, previous_loc=None: inf_yielder_weighted(
            candidates=candidates,
            weights=weights,
            transit_distance=transit_distance,
            max_walk=max_walk,
            transit_modes=transit_modes,
            expected_euclidean_speeds=expected_euclidean_speeds,
            mode=mode,
            previous_duration=previous_duration,
            previous_loc=previous_loc,
            seed=seed,
        )
    else:
        return inf_yielder_simple(candidates, seed=seed)


def inf_yielder_simple(
    candidates: list[tuple[Any, shapely.geometry.Point]], seed: Optional[int] = None
) -> Iterator[tuple[Any, shapely.geometry.Point]]:
    """Endlessly yield shuffled candidate items."""
    # Fix random seed
    random.seed(seed)
    while True:
        random.shuffle(candidates)
        for c in candidates:
            yield c


def inf_yielder_weighted(
    candidates: list[tuple[Any, shapely.geometry.Point]],
    weights: Optional[pd.Series],
    transit_distance: Optional[pd.Series],
    max_walk: Optional[float],
    transit_modes: Optional[list[str]],
    expected_euclidean_speeds: Optional[dict],
    mode: Optional[str],
    previous_duration: Optional[pd.Timedelta],
    previous_loc: Optional[shapely.geometry.Point],
    seed: Optional[int] = None,
) -> Iterator[tuple[Any, shapely.geometry.Point]]:
    """A more complex sampler, which allows for weighted and rule-based sampling (with replacement).

    Args:
        candidates (list[tuple[Any, shapely.geometry.Point]]): Tuples contain candidate facilities index values and their geolocation.
        weights (Optional[pd.Series]): sampling weights (ie facility floorspace).
        transit_distance (Optional[pd.Series]): distance of each candidate facility from the closest public transport (PT) stop.
        max_walk (Optional[float]): maximum walking distance from a PT stop.
        transit_modes (Optional[list[str]]): Possible transit modes.
        expected_euclidean_speeds (Optional[dict]):
        mode (Optional[str]):  transport mode used to access facility.
        previous_duration (Optional[pd.Timedelta]): the time duration of the arriving leg.
        previous_loc (Optional[shapely.geometry.Point]):  the location of the last visited activity.
        seed (Optional[int], optional):  If given, seed number for reproducible results. Defaults to None.


    Yields:
        Iterator[tuple[Any, shapely.geometry.Point]]:
    """
    # Fix random seed
    np.random.seed(seed)
    if isinstance(weights, pd.Series):
        # if a series of facility weights is provided, perform weighted sampling with replacement
        while True:
            ## if a transit mode is used and the distance from a stop is longer than the maximum walking distance,
            ## then replace the weight with a very small value
            if isinstance(transit_distance, pd.Series) and mode in transit_modes:
                weights = np.where(
                    transit_distance > max_walk,
                    weights
                    * variables.SMALL_VALUE,  # if no alternative is found within the acceptable range, the initial weights will be used
                    weights,
                )
            else:
                weights = weights.values

            # if the last location has been passed to the sampler, normalise by (expected) distance
            if previous_loc is not None:
                # calculate euclidean distance between the last visited location and every candidate location
                distances = np.array(
                    [euclidean_distance(previous_loc, candidate[1]) for candidate in candidates]
                )

                # calculate deviation from "expected" distance
                speed = (
                    expected_euclidean_speeds[mode]
                    if mode in expected_euclidean_speeds.keys()
                    else expected_euclidean_speeds["average"]
                )
                expected_distance = (
                    previous_duration / pd.Timedelta(seconds=1)
                ) * speed  # (in meters)
                distance_weights = np.abs(distances - expected_distance)
                distance_weights = np.where(
                    distance_weights == 0, variables.SMALL_VALUE, distance_weights
                )  # avoid having zero weights

                ## normalise weights by distance
                weights = weights / (distance_weights**2)  # distance decay factor of 2

            weights = weights / weights.sum()  # probability weights should add up to 1
            yield candidates[np.random.choice(len(candidates), p=weights)]
