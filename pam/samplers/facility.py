from typing import Union
from geopandas import GeoSeries, GeoDataFrame
from shapely.geometry import Point
import random


def random_point(idx: Union[int, str], geoms: Union[GeoSeries, GeoDataFrame], patience=100, fail=True):
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

    if isinstance(geoms, GeoSeries):
        point =  sample_point_from_polygon(geoms[idx], patience=patience)
        

    elif isinstance(geoms, GeoDataFrame):
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
