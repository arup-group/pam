import random
from collections.abc import Iterator

import geopandas as gp
import pandas as pd
import pytest
from pam.samplers import attributes, basic, facility, spatial
from shapely.geometry import (
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)


@pytest.fixture
def michael():
    return {"age": 16, "agebin": "younger", "gender": "male"}


@pytest.fixture
def kasia():
    return {"age": 96, "agebin": "older", "gender": "female"}


@pytest.fixture
def fred():
    return {"age": -3, "agebin": "", "gender": 1}


@pytest.fixture
def fixed_seed():
    return 1


@pytest.fixture
def fixed_seed2():
    return 10


@pytest.fixture
def bins():
    return {(0, 50): "younger", (51, 100): "older"}


@pytest.fixture
def cat_joint_distribution():
    mapping = ["agebin", "gender"]
    distribution = {"younger": {"male": 0, "female": 0}, "older": {"male": 0, "female": 1}}
    return mapping, distribution


@pytest.fixture
def dog_joint_distribution():
    mapping = ["agebin", "gender"]
    distribution = {"younger": {"male": 0.5, "female": 0.0}, "older": {"male": 0.0, "female": 0.5}}
    return mapping, distribution


def test_apply_bin_integer_transformer_to_michael(michael, bins):
    assert attributes.bin_integer_transformer(michael, "age", bins) == "younger"


def test_apply_bin_integer_transformer_with_missing_bin(fred, bins):
    assert attributes.bin_integer_transformer(fred, "age", bins) is None


def test_apply_discrete_joint_distribution_sampler_to_michael(michael, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(michael, mapping, dist) is False


def test_applt_discrete_joint_distribution_sampler_to_kasia(kasia, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(kasia, mapping, dist) is True


def test_applt_discrete_joint_distribution_sampler_to_fred_carefully(fred, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    with pytest.raises(KeyError):
        attributes.discrete_joint_distribution_sampler(fred, mapping, dist, careful=True)


def test_applt_discrete_joint_distribution_sampler_to_fred_not_carefully(
    fred, cat_joint_distribution
):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(fred, mapping, dist) is False


def test_random_seed_1(fixed_seed):
    random.seed(fixed_seed)
    assert random.random() <= 0.5


def test_random_seed_2(fixed_seed2):
    random.seed(fixed_seed2)
    assert random.random() >= 0.5


def test_applt_discrete_joint_distribution_sampler_reproducibility_to_michael_carefully(
    michael, dog_joint_distribution, fixed_seed
):
    mapping, dist = dog_joint_distribution
    assert (
        attributes.discrete_joint_distribution_sampler(
            michael, mapping, dist, careful=True, seed=fixed_seed
        )
        is True
    )


def test_applt_discrete_joint_distribution_sampler_reproducibility_to_kasia_carefully(
    kasia, dog_joint_distribution, fixed_seed2
):
    mapping, dist = dog_joint_distribution
    assert (
        attributes.discrete_joint_distribution_sampler(
            kasia, mapping, dist, careful=True, seed=fixed_seed2
        )
        is False
    )


testdata = [(0, 1.5, 0), (10, 1.0, 10), (0, 0.0, 0), (10, 2.0, 20), (10, 1.5, 15), (10, 0.5, 5)]


@pytest.mark.parametrize("freq,sample,result", testdata)
def test_freq_sampler_determined(freq, sample, result):
    assert basic.freq_sample(freq, sample) == result


testdata = [(1, 1.5, 1, 2), (1, 0.5, 0, 1), (1, 0.0001, 0, 1), (1, 1.0001, 1, 2)]


@pytest.mark.parametrize("freq,sample,lower,upper", testdata)
def test_freq_sampler_random_round(freq, sample, lower, upper):
    assert basic.freq_sample(freq, sample) in [lower, upper]


testdata = [(1, 1.5, 2), (1, 0.5, 1), (1, 0.0001, 0), (1, 1.0001, 1)]


@pytest.mark.parametrize("freq,sample,value", testdata)
def test_freq_sampler_random_round_fixed_seed(freq, sample, value, fixed_seed):
    assert basic.freq_sample(freq, sample, seed=fixed_seed) == value


def test_sample_point_from_geoseries_of_polygons():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry)
    assert isinstance(sampler.sample_point_from_polygon(gdf.geometry[0]), Point)


def test_sample_point_from_geoseries_of_polygons_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, seed=fixed_seed)
    assert list(sampler.sample_point_from_polygon(gdf.geometry[0]).coords[0]) == [
        0.13436424411240122,
        0.8474337369372327,
    ]


def test_sample_point_from_geoseries_of_polygons_invalid():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (0, 1), (1, 1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry)
    assert isinstance(sampler.sample_point_from_polygon(gdf.geometry[0]), Point)


def test_sample_point_from_geoseries_of_polygons_no_area():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (0, 0)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0)
    assert isinstance(sampler.sample_point_from_polygon(gdf.geometry[0]), Point)


def test_random_sample_point_from_multipolygon():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = Polygon(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiPolygon([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0)
    assert isinstance(sampler.sample_point_from_multipolygon(gdf.geometry[0]), Point)


def test_random_sample_point_from_multipolygon_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = Polygon(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiPolygon([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0, seed=fixed_seed)
    assert list(sampler.sample_point_from_multipolygon(gdf.geometry[0]).coords[0]) == [
        0.13436424411240122,
        0.8474337369372327,
    ]


def test_random_sample_point_from_multilinestring():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = LinearRing(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = LineString(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiLineString([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0)
    assert isinstance(sampler.sample_point_from_multilinestring(gdf.geometry[0]), Point)


def test_random_sample_point_from_multilinestring_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = LinearRing(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = LineString(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiLineString([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0, seed=fixed_seed)
    assert list(sampler.sample_point_from_multilinestring(gdf.geometry[0]).coords[0]) == [
        0.5374569764496049,
        0.0,
    ]


def test_random_sample_point_from_multipoint():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Point((0, 0))
    p2 = Point((10, 10))
    poly = MultiPoint([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0)
    assert isinstance(sampler.sample_point_from_multipoint(gdf.geometry[0]), Point)


def test_random_sample_point_from_multipoint_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Point((0, 0))
    p2 = Point((10, 10))
    poly = MultiPoint([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, patience=0, seed=fixed_seed)
    assert list(sampler.sample_point_from_multipoint(gdf.geometry[0]).coords[0]) == [0.0, 0.0]


def test_random_point_from_geoseries_of_polygons():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry)
    assert isinstance(sampler.sample(0, None), Point)


def test_random_point_from_geoseries_of_polygons_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    poly = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly] * 3)
    sampler = spatial.RandomPointSampler(gdf.geometry, seed=fixed_seed)
    assert sampler.sample(0, None).coords[0] == (0.13436424411240122, 0.8474337369372327)


def test_random_point_from_geodataframe_of_polygons():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = Polygon(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiPolygon([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[p1, p2, poly])
    sampler = spatial.RandomPointSampler(gdf)
    assert isinstance(sampler.sample(0, None), Point)
    assert isinstance(sampler.sample(1, None), Point)
    assert isinstance(sampler.sample(2, None), Point)


def test_random_point_from_geodataframe_of_polygons_random_seed(fixed_seed):
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = Polygon(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiPolygon([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[p1, p2, poly])
    sampler = spatial.RandomPointSampler(gdf, seed=fixed_seed)
    assert sampler.sample(0, None).coords[0] == (0.13436424411240122, 0.8474337369372327)
    assert sampler.sample(1, None).coords[0] == (10.134364244112401, 10.847433736937234)
    assert sampler.sample(2, None).coords[0] == (0.13436424411240122, 0.8474337369372327)


def test_random_point_from_geodataframe_of_lines():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = LinearRing(((0, 0), (1, 0), (1, 1), (0, 1)))
    p2 = LineString(((10, 10), (11, 10), (11, 11), (10, 11)))
    poly = MultiLineString([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[p1, p2, poly])
    sampler = spatial.RandomPointSampler(gdf)
    assert isinstance(sampler.sample(0, None), Point)
    assert isinstance(sampler.sample(1, None), Point)
    assert isinstance(sampler.sample(2, None), Point)


def test_random_point_from_geodataframe_of_points():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    p1 = Point((0, 0))
    p2 = Point((10, 10))
    poly = MultiPoint([p1, p2])
    gdf = gp.GeoDataFrame(df, geometry=[p1, p2, poly])
    sampler = spatial.RandomPointSampler(gdf)
    assert isinstance(sampler.sample(0, None), Point)
    assert isinstance(sampler.sample(1, None), Point)
    assert isinstance(sampler.sample(2, None), Point)


def test_random_point_fail():
    df = pd.DataFrame({1: [1, 2, 3], 2: [4, 5, 6]})
    gdf = gp.GeoDataFrame(df, geometry=[None] * 3)
    sampler = spatial.RandomPointSampler(gdf, fail=True, patience=0)
    with pytest.raises(AttributeError):
        sampler.sample(0, None)


def test_inf_yield():
    candidates = [1, 2, 3]
    sampler = facility.inf_yielder(candidates)
    assert set([next(sampler) for i in range(3)]) == set(candidates)
    assert set([next(sampler) for i in range(12)]) == set(candidates)
    assert len([i for i in [next(sampler) for i in range(12)] if i == 1]) == 4


def test_inf_yield_simple_random_seed(fixed_seed):
    candidates = [1, 2, 3]
    sampler = facility.inf_yielder(candidates, seed=fixed_seed)
    assert [next(sampler) for i in range(3)] == [2, 3, 1]


def test_inf_yield_weighted_random_seed(fixed_seed):
    candidates = [1, 2, 3]
    weights = pd.Series(data=[0.1, 0.2, 0.7], index=[1, 2, 3])
    sampler = facility.inf_yielder(candidates, weights=weights, seed=fixed_seed)
    assert [next(sampler(None, None, None)) for i in range(3)] == [3, 3, 3]


def test_facility_dict_build():
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(facility_gdf, zones_gdf, ["home", "work", "education"])
    assert len(sampler.samplers) == 2
    assert sampler.samplers[0]["education"] is None
    assert isinstance(sampler.samplers[0]["work"], Iterator)


def test_facility_sampler_normal():
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(facility_gdf, zones_gdf, ["home", "work", "education"])
    assert sampler.sample(0, "home") == Point((1, 1))


def test_facility_sampler_missing_activity_random_sample():
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(facility_gdf, zones_gdf, ["home", "work", "education"])
    assert isinstance(sampler.sample(0, "education"), Point)


def test_facility_sampler_missing_activity_random_sample_fixed_seed(fixed_seed):
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf, zones_gdf, ["home", "work", "education"], seed=fixed_seed
    )
    assert sampler.sample(0, "education").coords[0] == (0.26872848822480244, 1.6948674738744653)


def test_facility_sampler_missing_activity_return_None():
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf, zones_gdf, ["home", "work", "education"], random_default=False, fail=False
    )
    assert sampler.sample(0, "education") is None


def test_facility_sampler_missing_activity_fail():
    facility_df = pd.DataFrame(
        {"id": [1, 2, 3, 4], "activity": ["home", "work", "home", "education"]}
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf,
        zones_gdf,
        ["home", "work", "education"],
        random_default=False,
        fail=test_applt_discrete_joint_distribution_sampler_to_fred_not_carefully,
    )
    with pytest.raises(UserWarning):
        sampler.sample(0, "education")


def test_facility_sampler_weighted():
    # zero-weight home facility is ignored:
    facility_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "activity": ["home", "home", "home", "education"],
            "floorspace": [0, 200, 700, 100],
        }
    )
    points = [Point((1, 1)), Point((1.5, 1.5)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf, zones_gdf, ["home", "work", "education"], weight_on="floorspace"
    )
    assert sampler.sample(0, "home") == Point((1.5, 1.5))


def test_facility_sampler_weighted_maxwalk():
    # amongst three workplace alternatives, only one is within walking distance from a PT stop:
    facility_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "activity": ["work", "work", "work", "education"],
            "floorspace": [100000, 200000, 700, 100],
            "transit": [4000, 3000, 800, 10],
        }
    )
    points = [Point((1, 1)), Point((1.5, 1.5)), Point((1.8, 1.8)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf,
        zones_gdf,
        ["home", "work", "education"],
        weight_on="floorspace",
        max_walk=1000,
    )
    assert sampler.sample(0, "work", mode="bus") == Point((1.8, 1.8))


def test_facility_sampler_missing_activity_return_None_weighted():
    facility_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "activity": ["home", "work", "home", "education"],
            "floorspace": [0, 200, 700, 100],
        }
    )
    points = [Point((1, 1)), Point((1, 1)), Point((3, 3)), Point((3, 3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2), (2, 2), (2, 0))),
        Polygon(((2, 2), (2, 4), (4, 4), (4, 2))),
        Polygon(((4, 4), (4, 6), (6, 6), (6, 4))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf,
        zones_gdf,
        ["home", "work", "education"],
        random_default=False,
        fail=False,
        weight_on="floorspace",
    )
    assert sampler.sample(0, "education") is None


def test_facility_sampler_weighted_distance():
    # distance-based sampling
    # a 10-min walking trip at 5kph would have a radius of approx 1250 meters.
    facility_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "activity": ["work", "work", "work", "education"],
            "floorspace": [1, 1, 10, 10],
        }
    )
    points = [Point((0.01, 0.01)), Point((1000, 750)), Point((100, 100)), Point((30000, 30000))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    polys = [
        Polygon(((0, 0), (0, 2000), (2000, 2000), (2000, 0))),
        Polygon(((20000, 20000), (20000, 40000), (40000, 40000), (40000, 20000))),
        Polygon(((40000, 40000), (40000, 60000), (60000, 60000), (60000, 40000))),
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    sampler = facility.FacilitySampler(
        facility_gdf, zones_gdf, ["home", "work", "education"], weight_on="floorspace"
    )
    sampled_facilities = []
    for i in range(20):
        sampled_facilities.append(
            sampler.sample(
                0,
                "work",
                mode="walk",
                previous_duration=pd.Timedelta(minutes=15),
                previous_loc=Point(0, 0),
            )
        )
    assert pd.Series(sampled_facilities).value_counts(normalize=True).idxmax() == Point((1000, 750))
