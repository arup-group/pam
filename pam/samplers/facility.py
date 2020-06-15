from typing import Union
import geopandas as gp
from shapely.geometry import Point
import random
from lxml import etree as et

from pam.samplers.spatial import RandomPointSampler
from pam.utils import write_xml


class FacilitySampler:

    def __init__(
        self,
        facilities: gp.GeoDataFrame,
        zones: gp.GeoDataFrame,
        activities: list=None,
        build_xml: bool=True,
        fail: bool=True,
        random_default: bool=True
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
        """
        
        if activities is None:
            self.activities = list(set(facilities.activity))
        else:
            self.activities = activities

        self.samplers = self.build_facilities_sampler(facilities, zones, activities)
        self.build_xml = build_xml
        self.fail = fail
        self.random_default = random_default

        if random_default:
            self.random_sampler = RandomPointSampler(geoms=zones, fail=fail)

        self.facilities = {}
        self.index_counter = 0

    def sample(self, location_idx, activity):
        """
        Sample a shapely.Point from the given location and for the given activity.
        """

        idx, loc = self.sample_facility(location_idx, activity)

        if idx is not None and self.build_xml:
            self.facilities[idx] = {'loc': loc, 'act': activity}

        return loc

    def sample_facility(self, location_idx, activity):
        """
        Sample a facility id and location. If a location idx is missing, can return a random location.
        """
        if str(location_idx) not in self.samplers:
            if self.fail:
                raise IndexError(f'Cannot find idx: {location_idx} in facilities sampler')
            return None, None
        
        sampler = self.samplers[str(location_idx)][activity]

        if sampler is None:
            if self.random_default:
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
            return next(sampler)

    @staticmethod
    def build_facilities_sampler(facilities, zones, activities):
        """
        Build facility location sampler from osmfs input. The sampler returns a tuple of (uid, Point)
        TODO - I do not like having a sjoin and assuming index names here
        TODO - look to move to more carefully defined input data format for facilities
        """
        activity_areas = gp.sjoin(facilities, zones, how='inner', op='intersects')
        sampler_dict = {}

        for zone in set(activity_areas.index_right):
            zone_facs = activity_areas.loc[activity_areas.index_right == zone]
            sampler_dict[str(zone)] = {}
            for act in activities:
                points = [(i, g) for i, g in zone_facs.loc[zone_facs.activity == act].geometry.items()]
                if len(points):
                    sampler_dict[str(zone)][act] = inf_yielder(points)
                else:
                    sampler_dict[str(zone)][act] = None
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


def inf_yielder(candidates):
    """
    Endlessly yield shuffled candidate items.
    """
    while True:
        random.shuffle(candidates)
        for c in candidates:
            yield c
