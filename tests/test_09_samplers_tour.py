# %% import packages
import pytest
import random
import pandas as pd
import geopandas as gp
import numpy as np
from shapely.geometry import Point, Polygon
from matplotlib.figure import Figure

from pam.core import Person
from pam.samplers import tour
from pam.samplers.facility import FacilitySampler
from pam.variables import END_OF_DAY

# %% Test input data
facility_df = pd.DataFrame({'id':[1,2,3,4,5,6,7,8,9], 
                            'activity': ['home','delivery','home','depot', 'depot', 'depot', 'delivery', 'delivery', 'depot']})
points = [Point((1,1)), Point((1,2)), Point((1,3)), Point((1,4)),
          Point((2,1)), Point((2,2)), Point((2,3)), Point((2,4)),Point((4,6))]
facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)


zones_df = pd.DataFrame({'a':[1,2,3], 'b': [4,5,6], 'area':[7,8,0]})
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

depot_density = tour.create_density_gdf(facility_zone=facility_zone, zone=zones_gdf, activity=['depot'])
depot_normalised = tour.create_density_gdf(facility_zone=facility_zone, zone=zones_gdf, activity=['depot'], normalise='area')
delivery_density = tour.create_density_gdf(facility_zone=facility_zone, zone=zones_gdf, activity=['delivery'])

depot_sampler = tour.FrequencySampler(depot_density.index, depot_density.density)
hour_sampler = tour.FrequencySampler(range(24))
minute_sampler = tour.FrequencySampler(range(60))

trips = pd.DataFrame({'Unnamed: 0':[0, 1, 2, 3, 4],
                      'pid':['LGV_0', 'LGV_0', 'LGV_0', 'LGV_0', 'LGV_1'],
                      'ozone':[1,2,3,4,5],
                      'dzone':[1,1,1,1,0],
                      'origin activity':['depot', 'delivery', 'delivery', 'delivery', 'depot'],
                      'destination activity':['delivery', 'delivery', 'delivery', 'depot', 'delivery'],
                      'start_hour':[2, 3, 3, 3, 9]})

# %% 

def test_model_distance_value():
    assert tour.ActivityDuration().model_distance(Point((0,0)), Point((3,4)), scale=1) == 5


def test_model_journey_time_value():
    assert tour.ActivityDuration().model_journey_time(1000, 10) == 100
    assert tour.ActivityDuration().model_journey_time(50000, 40000/3600) == 4500


def test_distribution_uniform():
    bins = range(0,3)
    pivots = {0:1, 2:1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0]==10
    assert dist[1]==10
    assert dist[2]==10


def test_distribution_triangle():
    bins = range(0,3)
    pivots = {0:0, 2:1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0] == 0
    assert dist[1] == 10
    assert dist[2] == 20


def test_distribution_pivot_start_one():
    bins = range(0,3)
    pivots = {1:1, 2:1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0] == 0
    assert dist[1] == 15
    assert dist[2] == 15


def test_distribution_pivot_empty():
    bins = range(0,3)
    pivots = {}
    total = 30

    with pytest.raises(ZeroDivisionError, match='float division by zero'):
        dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand


def test_frequency_sampler_type():
    sampler = tour.FrequencySampler(range(60))
    assert isinstance(sampler.sample(), int)


def test_facility_density_missing_activity():

    assert len(depot_density.density) > 0
    assert len(delivery_density.density) > 0


def test_facility_density_normalised_differ_not_normalised():
    
    assert depot_normalised['density'][1] != depot_density['density'][1]


def test_facility_density_normalised_raises_warning_inf_values():
    with pytest.warns(UserWarning, match='Your density gdf has infinite values'):
        depot_normalised = tour.create_density_gdf(
                            facility_zone=facility_zone, 
                            zone=zones_gdf, 
                            activity=['depot'], 
                            normalise='area')


def test_dzone_sampler_dzone_d_density_zero():

    o_zone = 3
    threshold_value = 2

    with pytest.warns(UserWarning, match='No destinations within this threshold value, change threshold'):
        d_zone = tour.FrequencySampler(dist=delivery_density,
                                       freq='density',
                                       threshold_matrix=df_od[o_zone],
                                       threshold_value=threshold_value
                                       ).threshold_sample()


def test_frequency_sampler_with_density():
    zone_densities = pd.DataFrame({"zone": ["A", "B"], "density":[1, 0]}).set_index("zone")
    """
        density
    A   1
    B   0
    """
    assert tour.FrequencySampler(
        dist = zone_densities.index,
        freq = zone_densities.density,
        threshold_matrix = None,
        threshold_value = None
    ).sample() == "A"


def test_frequency_sampler_with_threshold():
    zone_densities = pd.DataFrame({"zone": ["A", "B"], "density":[1, 1]}).set_index("zone")
    """
        density
    A   1
    B   1
    """
    threshold_matrix = pd.DataFrame({"zone": ["A", "B"], "A":[0, 1000], "B":[1000, 0]}).set_index("zone")
    """
        A   B
    A   0   100
    B   100 0
    """
    assert tour.FrequencySampler(
        dist = zone_densities,
        freq = 'density',
        threshold_matrix = threshold_matrix["A"],
        threshold_value = 50
    ).threshold_sample() == "A"

def test_plot_pivot_distribution_sampler():
    bins = range(0,3)
    pivots = {1:1, 2:1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, 
                                         pivots=pivots, 
                                         total=total)
    fig = dist.plot(plot_title=f"Freight Distribution", 
                    x_label='Hour', 
                    y_label='Frequency')
    assert isinstance(fig, Figure)


# %%  Set parameters to validate Tour Planner
stops = 2
threshold_value = 6
o_zone = depot_sampler.sample()

agent_id = 'LGV_1'
agent = Person(
            agent_id,
            attributes={
                'subpopulation': 'lgv',
                'CarType': 'lgv',
                'CarCO2': 'lgv'
            }
        )

agent_plan = tour.TourPlanner(stops=stops,
                              hour=hour_sampler.sample(),
                              minute=minute_sampler.sample(),
                              o_zone=o_zone,
                              d_dist=delivery_density,
                              d_freq='density',
                              threshold_matrix=df_od,
                              threshold_value=threshold_value,
                              facility_sampler=facility_sampler,
                              activity_params={'o_activity':'depot', 'd_activity':'delivery'})

od_density = tour.ValidateTourOD(trips=trips,
                                      zone=zones_gdf,
                                      o_dist=depot_density,
                                      d_dist=delivery_density,
                                      o_activity='depot',
                                      d_activity='delivery',
                                      o_freq='density',
                                      d_freq='density'
                                      )
def test_sequence_stops_length():
    agent_plan_test = agent_plan
    o_loc, d_zones, d_locs = agent_plan_test.sequence_stops()

    assert len(d_locs) == stops


def test_activity_endtm_depot():
    agent_test = agent
    agent_plan_test = agent_plan

    o_loc, d_zones, d_locs = agent_plan_test.sequence_stops()
    time_params = {'hour': hour_sampler.sample(), 'minute': minute_sampler.sample()}
    end_tm = agent_plan_test.add_tour_activity(agent=agent_test, k=0, zone=o_zone, loc=o_loc, activity_type='depot', time_params=time_params)

    assert end_tm == ((time_params['hour']*60) + time_params['minute'])


def test_activity_endtm_notdepot():
    # ensure end_tm is calculated for the instance where tour is neither to depot or origin.
    agent = Person(
            agent_id,
            attributes={
                'subpopulation': 'lgv',
                'CarType': 'lgv',
                'CarCO2': 'lgv'
            }
        )

    agent_test = agent
    agent_plan_test = agent_plan

    o_loc, d_zones, d_locs = agent_plan_test.sequence_stops()
    time_params = {'end_tm': hour_sampler.sample(), 'stop_duration': minute_sampler.sample()}
    end_tm = agent_plan_test.add_tour_activity(agent=agent_test, k=0, zone=o_zone, loc=o_loc, activity_type='not_depot', time_params=time_params)

    assert end_tm == (time_params['end_tm'] + int(time_params['stop_duration']/60))


def test_activity_endtm_returnorigin():
    agent = Person(
            agent_id,
            attributes={
                'subpopulation': 'lgv',
                'CarType': 'lgv',
                'CarCO2': 'lgv'
            }
        )

    agent_test = agent
    agent_plan_test = agent_plan

    o_loc, d_zones, d_locs = agent_plan_test.sequence_stops()
    time_params = {'start_tm':0, 'end_tm': END_OF_DAY}
    end_tm = agent_plan_test.add_tour_activity(agent=agent_test, k=0, zone=o_zone, loc=o_loc, activity_type='return_origin', time_params=time_params)

    assert end_tm == END_OF_DAY


def test_final_activity_return_depot():
    agent_id = 'LGV_1'
    agent = Person(
            agent_id,
            attributes={
                'subpopulation': 'lgv',
                'CarType': 'lgv',
                'CarCO2': 'lgv'
            }
        )

    agent_plan_test = agent_plan
    o_loc, d_zones, d_locs = agent_plan.sequence_stops()
    agent_plan.apply(agent=agent, o_loc=o_loc, d_zones=d_zones, d_locs=d_locs)

    assert agent.plan[len(agent.plan)-1].act == 'depot'


def test_validatetourod_no_duplicates():

    assert depot_density.density.sum() == od_density.od_density.depot_density.sum()
    assert delivery_density.density.sum() == od_density.od_density.delivery_density.sum()


def test_plot_spatial_density():
    fig = od_density.plot_validate_spatial_density(title_1='Input Depot density', 
                                                   title_2='Output Depot density', 
                                                   density_metric='depot_density', 
                                                   density_trips='origin_trips')
    assert isinstance(fig, Figure)


def test_plot_compare_density():
    fig = od_density.plot_compare_density(title_1='Depot density vs. Origin', 
                                          title_2='Delivery density vs. Destination', 
                                          o_activity='depot_density', 
                                          d_activity='delivery_density')
    assert isinstance(fig, Figure)


def test_plot_density_difference():
    fig = od_density.plot_density_difference(title_1='Origin Difference', 
                                             title_2='Destination Difference')

    assert isinstance(fig, Figure)
