from unittest.case import DIFF_OMITTED
import pytest
import random
import pandas as pd
import geopandas as gp
from shapely.geometry import Point, Polygon
from scipy import spatial

from pam.core import Person
from pam.samplers import tour
from pam.samplers.facility import FacilitySampler
from pam.variables import END_OF_DAY

# Test input data
facility_df = pd.DataFrame({'id':[1,2,3,4], 'activity': ['home','delivery','home','depot']})
points = [Point((1,1)), Point((1,1)), Point((3,3)), Point((3,3))]
facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)


zones_df = pd.DataFrame({'a':[1,2,3], 'b': [4,5,6]})
polys = [
        Polygon(((0,0), (0,2), (2,2), (2,0))),
        Polygon(((2,2), (2,4), (4,4), (4,2))),
        Polygon(((4,4), (4,6), (6,6), (6,4)))
    ]

zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

facility_sampler = FacilitySampler(
    facilities=facility_gdf,
    zones=zones_gdf,
    build_xml=True,
    fail=False,
    random_default=True
)


def test_model_distance_value():
    assert tour.ActivityDuration().model_distance(Point((0,0)), Point((3,4)), scale=1) == 5

def test_model_journey_time_value():
    assert tour.ActivityDuration().model_journey_time(1000, 10) == 100
    assert tour.ActivityDuration().model_journey_time(50000, 40000/3600) == 4500


def test_distribution_type():
    bins = range(0,24)
    pivots = {1: 0, 2: 1, 8: 2, 15: 3}
    total = 100

    dist = tour.CreateDistribution().build_distribution(bins=bins, pivots=pivots, total=total)
    print(dist)
    
    assert isinstance(dist, dict)

def test_frequency_sampler_type():
    sampler = tour.FrequencySampler(range(60))
    assert isinstance(sampler.sample(), int)


def test_facility_density_missing_activity():
    o_density, d_density = tour.InputDemand().facility_density(facilities=facility_gdf,
                                                                      zones=zones_gdf,
                                                                      zone_id='a',
                                                                      o_activity='depot',
                                                                      d_activity='delivery')


    assert len(o_density) > 0
    assert len(d_density) > 0

def test_dzone_sampler_dzone_d_density_zero():
    o_density, d_density = tour.InputDemand().facility_density(facilities=facility_gdf,
                                                                zones=zones_gdf,
                                                                zone_id='a',
                                                                o_activity='depot',
                                                                d_activity='delivery')
    
    o_zone = 3
    zones_list = zones_gdf.centroid.apply(lambda x: [x.x, x.y]).to_list()
    od_matrix = spatial.distance_matrix(x=zones_list, y=zones_list)
    df_od = pd.DataFrame(od_matrix, index=zones_gdf.a, columns=zones_gdf.a)

    dist_threshold = df_od.median().agg('median')

    d_zone = tour.TourSequence().dzone_sampler(d_density=d_density,
                                               o_zone=o_zone,
                                               df_od=df_od,
                                               dist_threshold=dist_threshold,
                                               zone_id='a')
    
    assert d_zone == 0

def test_activity_endtm_endofday():
    agent_id = 'LGV_1'
    agent = Person(
            agent_id,
            attributes={
                'subpopulation': 'lgv',
                'CarType': 'lgv',
                'CarCO2': 'lgv'
            }
        )
    o_zone = random.choice(zones_gdf.a)
    o_loc = facility_sampler.sample(o_zone, 'depot')

    time_params = {'hour':tour.FrequencySampler(range(24)).sample(), 'minute':tour.FrequencySampler(range(60)).sample()}
    end_tm = tour.TourPlan().tour_activity(agent=agent, k=1, zone=o_zone, loc=o_loc, activity_type='depot', time_params=time_params)
    
    assert end_tm != END_OF_DAY