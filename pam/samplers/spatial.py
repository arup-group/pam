from typing import Union
import geopandas as gp
from shapely.geometry import Point
import random
import logging


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
        self.logger = logging.getLogger(__name__)

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
            self.logger.warning(f'Cannot find idx:{idx}, returning None')
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


class GeometryRandomSampler:
    def __init__(self, geo_df_file, geometry_name_column, default_region):
        self.geo_df = gp.read_file(geo_df_file)
        self.geometry_name_column = geometry_name_column
        self.default_region = default_region

        self.geo_df_loc_lookup = {value: key for (key, value) in self.geo_df[geometry_name_column].to_dict().items()}

        #Throws exception if default_region is invalid
        default_id = self.geo_df_loc_lookup[default_region]
        self.default_geom = self.geo_df.geometry.loc[default_id]

    def sample_point(self, geo_region, patience=1000):
        """
        **From Mimi
        Returns randomly placed point within given geometry, using the lsoa_df. Note that it uses
        random sampling within the shape's bounding box then checks if point is within given geometry.
        If the method cannot return a valid point within 50 attempts then a RunTimeWarning is raised.
        :param geo_name: name of a geometry in the object's geopandas dataframe
        :return: Point object
        """

        try:
            geo_id = self.geo_df_loc_lookup[geo_region]
            geom = self.geo_df.geometry.loc[geo_id]
        except KeyError:
            print('Unknown region: {}, sampling from {}'.format(geo_region, self.default_region))
            geom = self.default_geom

        min_x, min_y, max_x, max_y = geom.bounds
        for attempt in range(patience):
            random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if geom.is_valid:
                if random_point.within(geom):
                    return random_point
            else:
                if random_point.within(geom.buffer(0)):
                    return random_point

        raise RuntimeWarning(f'unable to sample point from geometry:{geo_region} with {patience} attempts')
