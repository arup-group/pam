# %% import packages

import geopandas as gp
import pandas as pd
import pytest
from matplotlib.figure import Figure
from pam.core import Person
from pam.samplers import tour
from pam.samplers.facility import FacilitySampler
from pam.variables import END_OF_DAY
from shapely.geometry import Point, Polygon

# %% Test input data


@pytest.fixture
def facility_gdf():
    facility_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "activity": [
                "home",
                "delivery",
                "home",
                "depot",
                "depot",
                "depot",
                "delivery",
                "delivery",
                "depot",
            ],
        }
    )
    points = [
        Point((0, 1000)),
        Point((0, 2000)),
        Point((1000, 1000)),
        Point((2000, 2000)),
        Point((2000, 1000)),
        Point((3000, 3000)),
        Point((5000, 4000)),
        Point((5000, 5000)),
        Point((6000, 4000)),
    ]
    return gp.GeoDataFrame(facility_df, geometry=points)


@pytest.fixture
def zones_gdf():
    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "area": [7, 8, 9]})
    polys = [
        Polygon(((0, 0), (0, 2000), (2000, 2000), (2000, 0))),
        Polygon(((2000, 2000), (2000, 4000), (4000, 4000), (4000, 2000))),
        Polygon(((4000, 4000), (4000, 6000), (6000, 6000), (6000, 4000))),
    ]

    gdf = gp.GeoDataFrame(zones_df, geometry=polys)
    gdf.set_index("a", inplace=True)
    return gdf


@pytest.fixture
def facility_zone(facility_gdf, zones_gdf):
    facility_zone = gp.sjoin(facility_gdf, zones_gdf, how="inner", predicate="intersects")
    facility_zone.rename(columns={"index_right": "a"}, inplace=True)
    facility_zone.set_index("a", inplace=True)
    return facility_zone


@pytest.fixture
def df_od(zones_gdf):
    od_matrix = [
        [0, 2828.427125, 5656.854249],
        [2828.427125, 0, 2828.427125],
        [5656.854249, 2828.427125, 0],
    ]
    return pd.DataFrame(od_matrix, index=zones_gdf.index, columns=zones_gdf.index)


@pytest.fixture
def facility_sampler(facility_gdf, zones_gdf):
    return FacilitySampler(
        facilities=facility_gdf, zones=zones_gdf, build_xml=True, fail=False, random_default=True
    )


@pytest.fixture
def depot_density(facility_zone, zones_gdf):
    return tour.create_density_gdf(facility_zone=facility_zone, zone=zones_gdf, activity=["depot"])


@pytest.fixture
def depot_normalised(facility_zone, zones_gdf):
    return tour.create_density_gdf(
        facility_zone=facility_zone, zone=zones_gdf, activity=["depot"], normalise="area"
    )


@pytest.fixture
def delivery_density(facility_zone, zones_gdf):
    return tour.create_density_gdf(
        facility_zone=facility_zone, zone=zones_gdf, activity=["delivery"]
    )


@pytest.fixture
def depot_sampler(depot_density):
    return tour.FrequencySampler(depot_density.index, depot_density.density)


@pytest.fixture
def hour_sampler():
    return tour.FrequencySampler(range(24))


@pytest.fixture
def minute_sampler():
    return tour.FrequencySampler(range(60))


@pytest.fixture
def trips():
    return pd.DataFrame(
        {
            "Unnamed: 0": [0, 1, 2, 3, 4],
            "pid": ["LGV_0", "LGV_0", "LGV_0", "LGV_0", "LGV_1"],
            "ozone": [1, 2, 3, 4, 5],
            "dzone": [1, 1, 1, 1, 0],
            "origin activity": ["depot", "delivery", "delivery", "delivery", "depot"],
            "destination activity": ["delivery", "delivery", "delivery", "depot", "delivery"],
            "start_hour": [2, 3, 3, 3, 9],
        }
    )


# %% testing Tour plan inputs (distance, distributions)
def test_model_distance_value():
    assert tour.model_distance(Point((0, 0)), Point((3, 4)), scale=1) == 5


def test_model_journey_time_value():
    assert tour.model_journey_time(1000, 10) == 100
    assert tour.model_journey_time(50000, 40000 / 3600) == 4500


def test_distribution_total_none():
    bins = range(0, 3)
    pivots = {0: 1, 2: 1}
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots)

    assert sum(dist.demand.values()) == 3


def test_distribution_total_not_zero():
    bins = range(0, 3)
    pivots = {0: 1, 2: 1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total)

    assert sum(dist.demand.values()) == 30


def test_distribution_uniform():
    bins = range(0, 3)
    pivots = {0: 1, 2: 1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0] == 10
    assert dist[1] == 10
    assert dist[2] == 10


def test_distribution_triangle():
    bins = range(0, 3)
    pivots = {0: 0, 2: 1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0] == 0
    assert dist[1] == 10
    assert dist[2] == 20


def test_distribution_pivot_start_one():
    bins = range(0, 3)
    pivots = {1: 1, 2: 1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand

    assert dist[0] == 0
    assert dist[1] == 15
    assert dist[2] == 15


def test_distribution_pivot_empty():
    bins = range(0, 3)
    pivots = {}
    total = 30

    with pytest.raises(ZeroDivisionError, match="float division by zero"):
        tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total).demand


def test_frequency_sampler_type():
    sampler = tour.FrequencySampler(range(60))
    assert isinstance(sampler.sample(), int)


def test_facility_density_missing_activity(depot_density, delivery_density):
    assert len(depot_density.density) > 0
    assert len(delivery_density.density) > 0


def test_facility_density_normalised_differ_not_normalised(depot_normalised, depot_density):
    assert depot_normalised["density"][1] != depot_density["density"][1]


def test_facility_density_normalised_raises_warning_inf_values(facility_zone, zones_gdf):
    zones_gdf.loc[3, "area"] = 0
    facility_zone.loc[3, "area"] = 0
    with pytest.warns(UserWarning, match="Your density gdf has infinite values"):
        tour.create_density_gdf(
            facility_zone=facility_zone, zone=zones_gdf, activity=["depot"], normalise="area"
        )


def test_dzone_sampler_dzone_d_density_zero(delivery_density, df_od):
    o_zone = 2
    threshold_value = 2000

    with pytest.warns(
        UserWarning, match="No destinations within this threshold value, change threshold"
    ):
        tour.FrequencySampler(
            dist=delivery_density,
            freq="density",
            threshold_matrix=df_od[o_zone],
            threshold_value=threshold_value,
        ).threshold_sample()


def test_frequency_sampler_with_density():
    zone_densities = pd.DataFrame({"zone": ["A", "B"], "density": [1, 0]}).set_index("zone")
    """
        density
    A   1
    B   0
    """
    assert (
        tour.FrequencySampler(
            dist=zone_densities.index,
            freq=zone_densities.density,
            threshold_matrix=None,
            threshold_value=None,
        ).sample()
        == "A"
    )


def test_frequency_sampler_with_threshold():
    zone_densities = pd.DataFrame({"zone": ["A", "B"], "density": [1, 1]}).set_index("zone")
    """
        density
    A   1
    B   1
    """
    threshold_matrix = pd.DataFrame({"zone": ["A", "B"], "A": [0, 1000], "B": [1000, 0]}).set_index(
        "zone"
    )
    """
        A   B
    A   0   100
    B   100 0
    """
    assert (
        tour.FrequencySampler(
            dist=zone_densities,
            freq="density",
            threshold_matrix=threshold_matrix["A"],
            threshold_value=50,
        ).threshold_sample()
        == "A"
    )


def test_plot_pivot_distribution_sampler():
    bins = range(0, 3)
    pivots = {1: 1, 2: 1}
    total = 30
    dist = tour.PivotDistributionSampler(bins=bins, pivots=pivots, total=total)
    fig = dist.plot(plot_title="Freight Distribution", x_label="Hour", y_label="Frequency")
    assert isinstance(fig, Figure)


# %%  Set parameters to validate Tour Planner
@pytest.fixture
def o_zone(depot_sampler):
    return depot_sampler.sample()


@pytest.fixture
def agent_plan(hour_sampler, minute_sampler, delivery_density, df_od, facility_sampler, o_zone):
    stops = 2
    threshold_value = 5000

    return tour.TourPlanner(
        stops=stops,
        hour=hour_sampler.sample(),
        minute=minute_sampler.sample(),
        o_zone=o_zone,
        d_dist=delivery_density,
        d_freq="density",
        threshold_matrix=df_od,
        threshold_value=threshold_value,
        facility_sampler=facility_sampler,
        activity_params={"o_activity": "depot", "d_activity": "delivery"},
    )


@pytest.fixture
def agent_plan_no_threshold(hour_sampler, minute_sampler, delivery_density, facility_sampler):
    stops = 2
    o_zone = 2

    return tour.TourPlanner(
        stops=stops,
        hour=hour_sampler.sample(),
        minute=minute_sampler.sample(),
        o_zone=o_zone,
        d_dist=delivery_density,
        d_freq="density",
        facility_sampler=facility_sampler,
        activity_params={"o_activity": "depot", "d_activity": "delivery"},
    )


@pytest.fixture
def agent_plan_exceed_24hrs(delivery_density, facility_sampler):
    stops = 2
    o_zone = 2

    return tour.TourPlanner(
        stops=stops,
        hour=23,
        minute=45,
        o_zone=o_zone,
        d_dist=delivery_density,
        d_freq="density",
        facility_sampler=facility_sampler,
        activity_params={"o_activity": "depot", "d_activity": "delivery"},
    )


@pytest.fixture
def d_facility_sampling(agent_plan_no_threshold):
    o_loc = agent_plan_no_threshold.facility_sampler.sample(
        agent_plan_no_threshold.o_zone, agent_plan_no_threshold.o_activity
    )
    d_seq = tour.TourPlanner.sample_destinations(agent_plan_no_threshold, o_loc)
    return o_loc, d_seq


@pytest.fixture
def sequenced_stops(agent_plan_no_threshold):
    o_loc, d_zones, d_locs = agent_plan_no_threshold.sequence_stops()
    return o_loc, d_zones, d_locs


@pytest.fixture(scope="function")
def agent():
    agent_id = "LGV_1"
    return Person(agent_id, attributes={"subpopulation": "lgv", "CarType": "lgv", "CarCO2": "lgv"})


@pytest.fixture
def od_density(trips, zones_gdf, depot_density, delivery_density):
    return tour.ValidateTourOD(
        trips=trips,
        zone=zones_gdf,
        o_dist=depot_density,
        d_dist=delivery_density,
        o_activity="depot",
        d_activity="delivery",
        o_freq="density",
        d_freq="density",
    )


def test_unique_stops(d_facility_sampling):
    o_loc, d_seq = d_facility_sampling

    # test for duplicate delivery locations in d_seq
    deliveries = set()
    for d in d_seq:
        d_point = d["destination_facility"]
        assert d_point not in deliveries, "Duplicate point found in d_seq"
        deliveries.add(d_point)


def test_origin_not_in_stops(d_facility_sampling):
    o_loc, d_seq = d_facility_sampling

    # test for duplicate delivery locations in d_seq
    deliveries = set()
    for d in d_seq:
        d_point = d["destination_facility"]
        deliveries.add(d_point)

    # test if o_loc is in d_seq
    assert o_loc not in deliveries, "o_loc has been sampled as a delivery location"


def test_distance_matrix_is_complete(agent_plan_no_threshold, d_facility_sampling):
    o_loc, d_seq = d_facility_sampling

    dist_matrix = tour.TourPlanner.create_distance_matrix(agent_plan_no_threshold, o_loc, d_seq)
    # Check for zero distances between different points
    for i in range(dist_matrix.shape[0]):
        for j in range(dist_matrix.shape[1]):
            if i != j:  # Check for non-diagonal entries
                assert (
                    dist_matrix[i, j] != 0
                ), "Zero distance found between different points in dist_matrix"


def test_sequence_stops_length(sequenced_stops):
    o_loc, d_zones, d_locs = sequenced_stops

    assert len(d_locs) == 2


def test_activity_endtm_depot(agent, agent_plan_no_threshold, hour_sampler, minute_sampler, o_zone):
    o_loc = Point(2000, 2000)
    time_params = {"hour": hour_sampler.sample(), "minute": minute_sampler.sample()}
    end_tm = agent_plan_no_threshold.add_tour_activity(
        agent=agent, k=0, zone=o_zone, loc=o_loc, activity_type="depot", time_params=time_params
    )

    assert end_tm == ((time_params["hour"] * 60) + time_params["minute"])


def test_activity_endtm_notdepot(
    agent, agent_plan_no_threshold, hour_sampler, minute_sampler, o_zone
):
    # ensure end_tm is calculated for the instance where tour is neither to depot or origin.
    o_loc = Point(2000, 2000)
    time_params = {"end_tm": hour_sampler.sample(), "stop_duration": minute_sampler.sample()}
    end_tm = agent_plan_no_threshold.add_tour_activity(
        agent=agent, k=0, zone=o_zone, loc=o_loc, activity_type="not_depot", time_params=time_params
    )

    assert end_tm == (time_params["end_tm"] + int(time_params["stop_duration"] / 60))


def test_activity_endtm_returnorigin(agent, agent_plan_no_threshold):
    o_loc = Point(2000, 2000)
    time_params = {"start_tm": 0, "end_tm": END_OF_DAY}
    end_tm = agent_plan_no_threshold.add_tour_activity(
        agent=agent,
        k=0,
        zone=o_zone,
        loc=o_loc,
        activity_type="return_origin",
        time_params=time_params,
    )

    assert end_tm == END_OF_DAY


def test_agent_first_activity_same_last_activity(agent, agent_plan_no_threshold):
    o_loc, d_zones, d_locs = agent_plan_no_threshold.sequence_stops()
    agent_plan_no_threshold.apply(agent=agent, o_loc=o_loc, d_zones=d_zones, d_locs=d_locs)

    assert agent.first_activity == agent.last_activity.act


def test_agent_last_leg_end_time_equal_last_activity_start(agent, agent_plan_no_threshold):
    o_loc, d_zones, d_locs = agent_plan_no_threshold.sequence_stops()
    agent_plan_no_threshold.apply(agent=agent, o_loc=o_loc, d_zones=d_zones, d_locs=d_locs)

    assert agent.last_leg.end_time == agent.last_leg.start_time + agent.last_leg.duration
    assert agent.last_leg.end_time == agent.last_activity.start_time


def test_agent_exceed_24hrs_last_activity_beyond_endofday(agent, agent_plan_exceed_24hrs):
    o_loc, d_zones, d_locs = agent_plan_exceed_24hrs.sequence_stops()
    agent_plan_exceed_24hrs.apply(agent=agent, o_loc=o_loc, d_zones=d_zones, d_locs=d_locs)

    assert agent.first_activity == agent.last_activity.act
    assert agent.last_leg.end_time > END_OF_DAY


def test_validatetourod_no_duplicates(depot_density, od_density, delivery_density):
    assert depot_density.density.sum() == od_density.od_density.depot_density.sum()
    assert delivery_density.density.sum() == od_density.od_density.delivery_density.sum()


def test_plot_spatial_density(od_density):
    fig = od_density.plot_validate_spatial_density(
        title_1="Input Depot density",
        title_2="Output Depot density",
        density_metric="depot_density",
        density_trips="origin_trips",
    )
    assert isinstance(fig, Figure)


def test_plot_compare_density(od_density):
    fig = od_density.plot_compare_density(
        title_1="Depot density vs. Origin",
        title_2="Delivery density vs. Destination",
        o_activity="depot_density",
        d_activity="delivery_density",
    )
    assert isinstance(fig, Figure)


def test_plot_density_difference(od_density):
    fig = od_density.plot_density_difference(
        title_1="Origin Difference", title_2="Destination Difference"
    )

    assert isinstance(fig, Figure)
