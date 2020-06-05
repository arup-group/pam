from typing import Union
import geopandas as gp
from shapely.geometry import Point
import random


def inf_yielder(candidates):
    """
    Endlessly yield shuffled candidate items.
    """
    while True:
        random.shuffle(candidates)
        for c in candidates:
            yield c


def build_facilities_sampler(facilities, census_areas, activities):
    """
    Build facility location sampler from osmfs input.
    """
    activity_areas = gp.sjoin(facilities, census_areas, how='inner', op='intersects')
    d = {}
    for zone in set(activity_areas.index_right):
        zone_facilities = activity_areas.loc[activity_areas.index_right == zone]
        d[zone] = {}
        for act in activities:
            points = list(zone_facilities.loc[zone_facilities.activity == act].geometry)
            if points:
                d[zone][act] = inf_yielder(points)
            else:
                d[zone][act] = None
    return d


class FaciltySampler:

    def __init__(self, facilities, census_areas, activities, build_xml=True, fail=True):
        self.activities = activities
        self.sampler = self.build_facilities_sampler(facilities, census_areas, activities)


    def sample_facility(sampler, location, activity, random_default=True):
        """
        Sample a facilkty location 
        """
        if idx not in self.sampler:
            print(f'could not find areas is {idx}')
            return None
        
        sampler = osm_sampler_dict[idx][act]
        if not sampler:
            if random_sampler:
                print(f'random_sample for {idx} {act}')
                return random_sampler(idx, areas)
        else:
            return next(sampler)

    @staticmethod
    def build_facilities_sampler(facilities, census_areas, activities):
        """
        Build facility location sampler from osmfs input.
        """
        activity_areas = gp.sjoin(facilities, census_areas, how='inner', op='intersects')
        d = {}
        for zone in set(activity_areas.index_right):
            zone_facilities = activity_areas.loc[activity_areas.index_right == zone]
            d[zone] = {}
            for act in activities:
                points = list(zone_facilities.loc[zone_facilities.activity == act].geometry)
                if points:
                    d[zone][act] = inf_yielder(points)
                else:
                    d[zone][act] = None
        return d


def random_point(idx: Union[int, str], geoms: Union[gp.GeoSeries, gp.GeoDataFrame], patience=100, fail=True):
    """
    Returns randomly placed point within given geometry, using geoms. Note that it uses
    random sampling within the shape's bounding box then checks if point is within given geometry.
    If the method cannot return a valid point within 'patience' attempts then either a RunTimeWarning 
    is raised or returns None.
    :param idx: index for geom identification
    :param geoms: GeoPandas or GeoSeries object
    :param patience: int, number of tries to sample point
    :param fail: Bool, option to raise error rather than return None
    :return: Point object or None
    """  

    if not idx in geoms.index:
        if fail:
            raise IndexError(f'Cannot find idx: {idx} in geoms (type: {type(geoms)})')
        return None

    if isinstance(geoms, gp.GeoSeries):
        point =  sample_point_from_polygon(geoms[idx], patience=patience)
        

    elif isinstance(geoms, gp.GeoDataFrame):
        point =  sample_point_from_polygon(geoms.geometry[idx], patience=patience)

    else:
        raise UserWarning(f"Failed to sample location for geom idx:{idx}, unknown datatype: {type(geoms)}")

    if point is None and fail:
        raise TimeoutError(f"Failed to find point for geom idx: {idx}")
    return point


def sample_point_from_polygon(poly, patience=100):

    if not poly.is_valid:
        poly.buffer(0)

    min_x, min_y, max_x, max_y = poly.bounds
    for _ in range(patience):
        random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
        if random_point.within(poly):
            return random_point

    return None


