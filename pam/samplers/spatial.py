import logging
import random
from typing import Union

import geopandas as gp
from shapely.geometry import Point


class RandomPointSampler:
    def __init__(
        self, geoms: Union[gp.GeoSeries, gp.GeoDataFrame], patience=100, fail=True, seed: int = None
    ):
        """Returns randomly placed point within given geometries, as defined by geoms. Note that it uses
        random sampling within the shape's bounding box then checks if point is within given geometry.
        If the method cannot return a valid point within 'patience' attempts then either a RunTimeWarning
        is raised or returns None.
        :param geoms: GeoPandas or GeoSeries object
        :param patience: int, number of tries to sample point
        :param fail: Bool, option to raise error rather than return None
        :params int seed: seed number for reproducible results (None default - does not fix seed).
        """
        self.logger = logging.getLogger(__name__)

        self.index = list(geoms.index)

        if isinstance(geoms, gp.GeoSeries):
            self.geoms = geoms

        elif isinstance(geoms, gp.GeoDataFrame):
            self.geoms = geoms.geometry

        else:
            raise UserWarning(
                f"Unknown datatype: {type(geoms)}, please use GeoSeries or GeoDataFrame"
            )

        self.patience = patience
        self.fail = fail
        # Store random seed
        self.seed = seed

    def sample(self, idx: Union[int, str], activity):
        """:param idx: index for geom index
        :return: Point object or None
        """
        if idx not in self.index:
            if self.fail:
                raise IndexError(f"Cannot find idx: {idx} in geoms index")
            self.logger.warning(f"Cannot find idx:{idx}, returning None")
            return None

        geom = self.geoms[idx]

        if not geom.is_valid:
            geom.buffer(0)

        if geom.geom_type == "Polygon":
            return self.validate_return(self.sample_point_from_polygon(geom), idx)

        if geom.geom_type == "MultiPolygon":
            return self.validate_return(self.sample_point_from_multipolygon(geom), idx)

        if geom.geom_type == "LineString" or geom.geom_type == "LinearRing":
            return self.validate_return(self.sample_point_from_linestring(geom), idx)

        if geom.geom_type == "MultiLineString":
            return self.validate_return(self.sample_point_from_multilinestring(geom), idx)

        if geom.geom_type == "Point":
            return self.validate_return(self.sample_point_from_point(geom), idx)

        if geom.geom_type == "MultiPoint":
            return self.validate_return(self.sample_point_from_multipoint(geom), idx)

        self.logger.warning(f"Unknown geom type {geom.geom_type}, attempting to sample.")

        return self.validate_return(self.sample_point_from_polygon(geom), idx)

    def validate_return(self, point, idx):
        if point is None and self.fail:
            raise TimeoutError(f"Failed to sample point for geom idx: {idx}")
        return point

    def sample_point_from_point(self, geom):
        return geom

    def sample_point_from_multipoint(self, geom):
        # Fix random seed
        random.seed(self.seed)
        return random.choice(list(geom.geoms))

    def sample_point_from_linestring(self, geom):
        """Also works for linearRing."""
        # Fix random seed
        random.seed(self.seed)
        return geom.interpolate(random.random(), True)

    def sample_point_from_multilinestring(self, geom):
        # Fix random seed
        random.seed(self.seed)
        line = random.choice(list(geom.geoms))
        return self.sample_point_from_linestring(line)

    def sample_point_from_polygon(self, geom):
        """Return random coordinates within polygon, note that will return float coordinates."""
        # Fix random seed
        random.seed(self.seed)
        min_x, min_y, max_x, max_y = geom.bounds
        for _ in range(self.patience):
            random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if random_point.within(geom):
                return random_point

        return Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))

    def sample_point_from_multipolygon(self, geom):
        # Fix random seed
        random.seed(self.seed)
        poly = random.choices(geom.geoms, weights=[poly.area for poly in geom.geoms])[0]
        return self.sample_point_from_polygon(poly)


class GeometryRandomSampler:
    def __init__(self, geo_df_file, geometry_name_column, default_region, seed: int = None):
        """:params int seed: seed number for reproducible results (None default - does not fix seed)"""
        self.geo_df = gp.read_file(geo_df_file)
        self.geometry_name_column = geometry_name_column
        self.default_region = default_region

        self.geo_df_loc_lookup = {
            value: key for (key, value) in self.geo_df[geometry_name_column].to_dict().items()
        }

        # Throws exception if default_region is invalid
        default_id = self.geo_df_loc_lookup[default_region]
        self.default_geom = self.geo_df.geometry.loc[default_id]

        # Store random seed
        self.seed = seed

    def sample_point(self, geo_region, patience=1000):
        """**From Mimi
        Returns randomly placed point within given geometry, using the lsoa_df. Note that it uses
        random sampling within the shape's bounding box then checks if point is within given geometry.
        If the method cannot return a valid point within 50 attempts then a RunTimeWarning is raised.
        :param geo_name: name of a geometry in the object's geopandas dataframe
        :return: Point object.
        """
        try:
            geo_id = self.geo_df_loc_lookup[geo_region]
            geom = self.geo_df.geometry.loc[geo_id]
        except KeyError:
            print("Unknown region: {}, sampling from {}".format(geo_region, self.default_region))
            geom = self.default_geom

        # Fix random seed
        random.seed(self.seed)

        min_x, min_y, max_x, max_y = geom.bounds
        for attempt in range(patience):
            random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if geom.is_valid:
                if random_point.within(geom):
                    return random_point
            else:
                if random_point.within(geom.buffer(0)):
                    return random_point

        raise RuntimeWarning(
            f"unable to sample point from geometry:{geo_region} with {patience} attempts"
        )
