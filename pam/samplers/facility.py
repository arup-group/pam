from typing import Union
import geopandas as gp
from shapely.geometry import Point
import random
from lxml import etree as et
import logging

from pam.samplers.spatial import RandomPointSampler
from pam.utils import write_xml
from pam import variables

import pandas as pd
import numpy as np
import pickle
from types import GeneratorType

class FacilitySampler:

    def __init__(
        self,
        facilities: gp.GeoDataFrame,
        zones: gp.GeoDataFrame,
        activities: list=None,
        build_xml: bool=True,
        fail: bool=True,
        random_default: bool=True,
        weight_on: str=None,
        max_walk: float=None,
        transit_modes: list=None,
        expected_euclidean_speeds: dict=None,
        activity_areas_path: str=None
        ):
        """
        Sampler object for facilities. optionally build a facility xml output (for MATSim).
        Note that if a zone id is missing then the sampler will not be able to default to 
        random sample, so will either return None or fail as per the fail flag.
        :param facilities: facilities Geodataframe
        :param zones: zones Geodataframe
        :param activities: optionally set list of subset of activities to be considered
        :param build_xml: flag for facility xml output (for MATSim)
        :param fail: flag hard fail if sample not found
        :param random_default: flag for defaulting to random sample when activity missing
        :param weight_on: the column name of the facilities geodataframe which contains facility weights (for sampling)
        :param max_walk: maximum walking distnace from a transit stop
        :param list transit_modes: a list of PT modes. If not specified, the default list in variables.TRANSIT_MODES is used
        :param list expected_euclidean_speeds: a dictionary specifying the euclidean speed of the various modes (m/s). If not specified, the default list in variables.EXPECTED_EUCLIDEAN_SPEEDS is used
        :param str activity_areas_path: path to the activity areas shapefile (previously exported throught the FacilitySampler.export_activity_areas method)
        """
        self.logger = logging.getLogger(__name__)
        
        if activities is None:
            self.activities = list(set(facilities.activity))
        else:
            self.activities = activities

        ## overrides for transit mode and speed specifications
        self.TRANSIT_MODES = transit_modes if transit_modes is not None else variables.TRANSIT_MODES
        self.EXPECTED_EUCLIDEAN_SPEEDS = expected_euclidean_speeds if expected_euclidean_speeds is not None else variables.EXPECTED_EUCLIDEAN_SPEEDS

        # spatial join
        if activity_areas_path is None:
            self.activity_areas = self.spatial_join(facilities, zones)
        else:
            self.load_activity_areas(activity_areas_path)

        # build samplers
        self.samplers = self.build_facilities_sampler(self.activity_areas, weight_on = weight_on, max_walk = max_walk)
        self.build_xml = build_xml
        self.fail = fail
        self.random_default = random_default

        if random_default:
            self.random_sampler = RandomPointSampler(geoms=zones, fail=fail)

        self.facilities = {}
        self.index_counter = 0
        self.error_counter = 0


    def clear(self):
        self.facilities = {}

    def sample(self, location_idx, activity, mode=None, previous_duration=None, previous_loc=None):
        """
        Sample a shapely.Point from the given location and for the given activity.
        :params str location_idx: the zone to sample from
        :params str activity: activity purpose
        :params str mode: transport mode used to access facility
        :params pd.Timedelta previous_duration: the time duration of the arriving leg
        :params shapely.Point previous_loc: the location of the last visited activity
        """

        idx, loc = self.sample_facility(location_idx, activity, mode=mode, previous_duration=previous_duration, previous_loc=previous_loc)

        if idx is not None and self.build_xml:
            self.facilities[idx] = {'loc': loc, 'act': activity}

        return loc

    def sample_facility(self, location_idx, activity, patience=1000, mode=None, previous_duration=None, previous_loc=None):
        """
        Sample a facility id and location. If a location idx is missing, can return a random location.
        """
        if location_idx not in self.samplers:
            if self.random_default:
                self.logger.warning(f"Using random sample for zone:{location_idx}:{activity}")
                idx = f"_{self.index_counter}"
                self.index_counter += 1
                return idx, self.random_sampler.sample(location_idx)
            if self.fail:
                raise IndexError(f'Cannot find idx: {location_idx} in facilities sampler')
            self.logger.warning(f'Missing location idx:{location_idx}')
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
                return idx, self.random_sampler.sample(location_idx)
            elif self.fail:
                raise UserWarning(
            f'Cannot find activity: {activity} in location: {location_idx}, consider allowing random default.'
            )
            else:
                return None, None
        else:
            self.error_counter = 0
            if isinstance(sampler, GeneratorType):
                return next(sampler)
            else:
                return next(sampler(mode, previous_duration, previous_loc))

    def spatial_join(self, facilities, zones):
        """
        Spatially join facility and zone data
        """
        self.logger.warning("Joining facilities data to zones, this may take a while.")
        return gp.sjoin(facilities, zones, how='inner', op='intersects')

    def export_activity_areas(self, filepath):
        """
        Export the spatially joined facilities-zones geodataframe
        """
        with open(filepath, 'wb') as f:
            pickle.dump(self.activity_areas, f)

    def load_activity_areas(self, filepath):
        """
        Load the spatially joined facilities-zones geodataframe
        """
        with open(filepath, 'rb') as f:
            self.activity_areas = pickle.load(f)

    def build_facilities_sampler(self, activity_areas, weight_on = None, max_walk = None):
        """
        Build facility location sampler from osmfs input. The sampler returns a tuple of (uid, Point)
        TODO - I do not like having a sjoin and assuming index names here
        TODO - look to move to more carefully defined input data format for facilities

        :params str weight_on: a column (name) of the facilities geodataframe to be used as a sampling weight
        """
        activity_areas = self.activity_areas
        sampler_dict = {}

        self.logger.warning("Building sampler, this may take a while.")
        for zone in set(activity_areas.index_right):
            sampler_dict[zone] = {}
            zone_facs = activity_areas.loc[activity_areas.index_right == zone]
            
            for act in self.activities:
                self.logger.debug(f"Building sampler for zone:{zone} act:{act}.")
                facs = zone_facs.loc[zone_facs.activity == act]
                if not facs.empty:
                    points = [(i, g) for i, g in facs.geometry.items()]
                    if weight_on is not None:
                        # weighted sampler
                        weights = facs[weight_on]
                        transit_distance = facs['transit'] if max_walk is not None else None
                        sampler_dict[zone][act] = inf_yielder(points, weights, transit_distance, max_walk, self.TRANSIT_MODES, self.EXPECTED_EUCLIDEAN_SPEEDS)
                    else:
                        # simple sampler
                        sampler_dict[zone][act] = inf_yielder(points)
                else:
                    sampler_dict[zone][act] = None
        return sampler_dict

    def write_facilities_xml(self, path, comment=None):

        facilities_xml = et.Element('facilities')

        # Add some useful comments
        if comment:
            facilities_xml.append(et.Comment(comment))
        # facilities_xml.append(et.Comment(f"Created {datetime.today()}"))

        for i, data in self.facilities.items():

            facility_xml = et.SubElement(
                facilities_xml,
                'facility',
                {'id':str(i), "x" : str(data['loc'].x), "y" : str(data['loc'].y)}
                )

            act_xml = et.SubElement(
                facility_xml,
                'activity',
                {"type" : data['act']})

        write_xml(
            facilities_xml,
            location=path,
            matsim_DOCTYPE='facilities',
            matsim_filename='facilities_v1'
            )

def euclidean_distance(p1, p2):
    """
    Calculate euclidean distance between two Activity.location.loc objects
    """
    return ((p1.x-p2.x)**2 + (p1.y-p2.y)**2)**0.5


def inf_yielder(candidates, weights = None, transit_distance=None, max_walk=None, transit_modes=None, expected_euclidean_speeds=None):
    """
    Redirect to the appropriate sampler.
    :params list candidates: a list of tuples, containing candidate facilities and their index:
    :params pd.Series weights: sampling weights (ie facility floorspace)
    :params pd.Series transit_distance: distance of each candidate facility from the closest PT stop
    :params float max_walk: maximum walking distance from a PT stop
    """
    if isinstance(weights, pd.Series):
        return lambda mode = None, previous_duration = None, previous_loc = None: inf_yielder_weighted(
                candidates = candidates, 
                weights = weights, 
                transit_distance = transit_distance, 
                max_walk = max_walk,
                transit_modes=transit_modes,
                expected_euclidean_speeds=expected_euclidean_speeds,
                mode = mode, 
                previous_duration = previous_duration, 
                previous_loc = previous_loc
            )
    else:
        return inf_yielder_simple(candidates)

def inf_yielder_simple(candidates):
    """
    Endlessly yield shuffled candidate items.
    """
    while True:
        random.shuffle(candidates)
        for c in candidates:
            yield c

def inf_yielder_weighted(candidates, weights, transit_distance, max_walk, transit_modes, expected_euclidean_speeds, mode, previous_duration, previous_loc):
    """
    A more complex sampler, which allows for weighted and rule-based sampling (with replacement).
    :params list candidates: a list of tuples, containing candidate facilities and their index:
    :params pd.Series weights: sampling weights (ie facility floorspace)
    :params pd.Series transit_distance: distance of each candidate facility from the closest PT stop
    :params float max_walk: maximum walking distance from a PT stop
    :params str mode: transport mode used to access facility
    :params pd.Timedelta previous_duration: the time duration of the arriving leg
    :params shapely.Point previous_loc: the location of the last visited activity
    """

    if isinstance(weights, pd.Series):
        # if a series of facility weights is provided, perform weighted sampling with replacement
        while True:

            ## if a transit mode is used and the distance from a stop is longer than the maximum walking distance,
            ## then replace the weight with a very small value
            if isinstance(transit_distance, pd.Series) and mode in transit_modes:
                weights = np.where(
                    transit_distance > max_walk,
                    weights * variables.SMALL_VALUE, # if no alternative is found within the acceptable range, the initial weights will be used
                    weights
                )
                
            # if the last location has been passed to the sampler, normalise by (expected) distance
            if previous_loc is not None:
                
                # calculate euclidean distance between the last visited location and every candidate location
                distances = np.array([euclidean_distance(previous_loc, candidate[1]) for candidate in candidates])

                # calculate deviation from "expected" distance
                speed = expected_euclidean_speeds[mode] if mode in expected_euclidean_speeds.keys() else expected_euclidean_speeds['average']
                expected_distance = (previous_duration / pd.Timedelta(seconds=1)) * speed  # (in meters)
                distance_weights = np.abs(distances - expected_distance)
                distance_weights = np.where(distance_weights==0, variables.SMALL_VALUE, distance_weights) # avoid having zero weights

                ## normalise weights by distance            
                # weights = weights.values / np.exp(distance_weights) # exponentiate distances to reduce the effect very small distances 
                # weights = weights.values / np.exp(distance_weights/distance_weights.max())          
                # weights = weights / (1 + np.exp(1*(distance_weights - distance_weights.mean()))) # alternative formulation: logistic curve
                # weights = weights.values / (1 + np.exp((distance_weights))) # alternative formulation: logistic curve   
                weights = weights.values / (distance_weights ** 2) # distance decay factor of 2 

            weights = weights / weights.sum() # probability weights should add up to 1

            yield candidates[np.random.choice(len(candidates), p = weights)]

