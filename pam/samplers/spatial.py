from typing import Union
import geopandas as gp
from shapely.geometry import Point
import random


class RandomPointSampler:

    def __init__(self, geoms: Union[gp.GeoSeries, gp.GeoDataFrame], patience=100, fail=True):
        """
        Returns randomly placed point within given geometries, as defined by geoms. Note that it uses
        random sampling within the shape's bounding box then checks if point is within given geometry.
        If the method cannot return a valid point within 'patience' attempts then either a RunTimeWarning 
        is raised or returns None.
        :param geoms: GeoPandas or GeoSeries object
        :param patience: int, number of tries to sample point
        :param fail: Bool, option to raise error rather than return None
        """

        self.index = list(geoms.index)

        if isinstance(geoms, gp.GeoSeries):
            self.geoms = geoms 

        elif isinstance(geoms, gp.GeoDataFrame):
            self.geoms = geoms.geometry
        
        else:
            raise UserWarning(f"Unknown datatype: {type(geoms)}, please use GeoSeries or GeoDataFrame")

        self.patience = patience
        self.fail = fail

    def sample(self, idx: Union[int, str]):
        """
        :param idx: index for geom index
        :return: Point object or None
        """  

        if not idx in self.index:
            if self.fail:
                raise IndexError(f'Cannot find idx: {idx} in geoms index')
            return None

        point =  self.sample_point_from_polygon(self.geoms[idx])

        if point is None and self.fail:
            raise TimeoutError(f"Failed to sample point for geom idx: {idx}")
        return point


    def sample_point_from_polygon(self, poly):
        """
        Return random coordinates within polygon, note that will return float coordinates.
        """
        if not poly.is_valid:
            poly.buffer(0)

        min_x, min_y, max_x, max_y = poly.bounds
        for _ in range(self.patience):
            random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if random_point.within(poly):
                return random_point

        return None