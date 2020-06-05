import random
import geopandas as gp
from shapely.geometry import Point

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

        raise RuntimeWarning(f'unable to sample point from geometry:{geo_id} with {patience} attempts')
