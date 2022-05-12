from unittest.case import DIFF_OMITTED
import pytest
import random
import pandas as pd
import geopandas as gp
from shapely.geometry import Point, Polygon

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
zones_gdf.set_index('a', inplace=True)

facility_zone = gp.sjoin(facility_gdf, zones_gdf, how='inner', predicate='intersects')
facility_zone.rename(columns={'index_right':'a'}, inplace = True)
facility_zone.set_index('a', inplace = True)

od_matrix = [[0, 2.82842712, 5.65685425], [2.82842712, 0, 2.82842712],[5.65685425, 2.82842712, 0]]
df_od = pd.DataFrame(od_matrix, index=zones_gdf.index, columns=zones_gdf.index)

facility_sampler = FacilitySampler(
    facilities=facility_gdf,
    zones=zones_gdf,
    build_xml=True,
    fail=False,
    random_default=True
)

trips = pd.DataFrame({'Unnamed: 0':[0, 1, 2, 3, 4],
                      'pid':['LGV_0', 'LGV_0', 'LGV_0', 'LGV_0', 'LGV_1'],
                      'ozone':[1,2,3,4,5],
                      'dzone':[1,1,1,1,0],
                      'origin activity':['depot', 'delivery', 'delivery', 'delivery', 'depot'],
                      'destination activity':['delivery', 'delivery', 'delivery', 'depot', 'delivery'],
                      'start_hour':[2, 3, 3, 3, 9]})

def test_model_distance_value():
    assert tour.ActivityDuration().model_distance(Point((0,0)), Point((3,4)), scale=1) == 5

def test_model_journey_time_value():
    assert tour.ActivityDuration().model_journey_time(1000, 10) == 100
    assert tour.ActivityDuration().model_journey_time(50000, 40000/3600) == 4500


def test_distribution_type():
    bins = range(0,24)
    pivots = {1: 0, 2: 1, 8: 2, 15: 3}
    total = 100

    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total)
    print(dist.demand)
    
    assert isinstance(dist.demand, dict)

def test_frequency_sampler_type():
    sampler = tour.FrequencySampler(range(60))
    assert isinstance(sampler.sample(), int)


def test_facility_density_missing_activity():
    o_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'depot')
    d_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'delivery')

    assert len(o_density.density) > 0
    assert len(d_density.density) > 0

def test_dzone_sampler_dzone_d_density_zero():
    d_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'delivery')
    o_zone = 3
    dist_threshold = df_od.median().agg('median')

    with pytest.raises(UserWarning, match='No destinations within this distance'):
        d_zone = d_density.dzone_sample(o_zone=o_zone, df_od=df_od, dist_threshold=dist_threshold)

def test_sequence_stops_length():
    stops=2
    o_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'depot')
    d_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'delivery')
    dist_threshold = 6

    o_zone, o_loc, d_zone, d_loc = tour.TourPlan().sequence_stops(stops=stops,
                                                                ozone_sampler=o_density,
                                                                dzone_sampler=d_density,
                                                                df_od=df_od,
                                                                dist_threshold=dist_threshold,
                                                                dist_id='distance',
                                                                facility_sampler=facility_sampler,
                                                                o_activity='depot',
                                                                d_activity='delivery')
    assert print(len(d_loc)) == print(stops)


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
    o_zone = random.choice(zones_gdf.index)
    o_loc = facility_sampler.sample(o_zone, 'depot')

    time_params = {'hour':tour.FrequencySampler(range(22)).sample(), 'minute':tour.FrequencySampler(range(60)).sample()}
    end_tm = tour.TourPlan().add_tour_activity(agent=agent, k=1, zone=o_zone, loc=o_loc, activity_type='depot', time_params=time_params)
    
    assert end_tm != END_OF_DAY

def test_validatetourod_no_duplicates():
    o_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'depot')
    d_density = tour.FacilityDensitySampler(facility_zone=facility_zone, zone=zones_gdf, activity = 'delivery')
    od_density = tour.ValidateTourOD(trips=trips,
                                      zone=zones_gdf,
                                      ozone_sampler=o_density,
                                      dzone_sampler=d_density,
                                      o_activity='depot',
                                      d_activity='delivery'
                                      )
    
    assert o_density.density.density.sum() == od_density.od_density.depot_density.sum()
    assert d_density.density.density.sum() == od_density.od_density.delivery_density.sum()