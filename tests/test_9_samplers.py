import pytest
import pandas as pd
import geopandas as gp
from shapely.geometry import Polygon, Point

from pam.samplers import attributes, basic, facility


@pytest.fixture
def michael():

    return {
        'age': 16,
        'agebin': 'younger',
        'gender': 'male'
    }


@pytest.fixture
def kasia():

    return {
        'age': 96,
        'agebin': 'older',
        'gender': 'female'
    }


@pytest.fixture
def fred():

    return {
        'age': -3,
        'agebin': '',
        'gender': 1
    }


@pytest.fixture
def bins():

    return {
        (0,50): 'younger',
        (51,100): 'older'
    }


@pytest.fixture
def cat_joint_distribution():

    mapping = ['agebin', 'gender']
    distribution = {
        'younger': {'male': 0, 'female': 0},
        'older': {'male': 0, 'female': 1}
    }
    return mapping, distribution


def test_apply_bin_integer_transformer_to_michael(michael, bins):
    assert attributes.bin_integer_transformer(michael, 'age', bins) == 'younger'


def test_apply_bin_integer_transformer_with_missing_bin(fred, bins):
    assert attributes.bin_integer_transformer(fred, 'age', bins) is None


def test_apply_discrete_joint_distribution_sampler_to_michael(michael, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(michael, mapping, dist) == False


def test_applt_discrete_joint_distribution_sampler_to_kasia(kasia, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(kasia, mapping, dist) == True


def test_applt_discrete_joint_distribution_sampler_to_fred_carefully(fred, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    with pytest.raises(KeyError):
        attributes.discrete_joint_distribution_sampler(fred, mapping, dist, careful=True)


def test_applt_discrete_joint_distribution_sampler_to_fred_not_carefully(fred, cat_joint_distribution):
    mapping, dist = cat_joint_distribution
    assert attributes.discrete_joint_distribution_sampler(fred, mapping, dist) == False


testdata = [
    (0, 1.5, 0),
    (10, 1., 10),
    (0, 0.0, 0),
    (10, 2., 20),
    (10, 1.5, 15),
    (10, .5, 5),
]
@pytest.mark.parametrize("freq,sample,result", testdata)
def test_freq_sampler_determined(freq,sample,result):
    assert basic.freq_sample(freq, sample) == result


testdata = [
    (1, 1.5, 1, 2),
    (1, .5, 0, 1),
    (1, 0.0001, 0, 1),
    (1, 1.0001, 1, 2),
]
@pytest.mark.parametrize("freq,sample,lower,upper", testdata)
def test_freq_sampler_random_round(freq, sample, lower, upper):
    assert basic.freq_sample(freq, sample) in [lower, upper]


def test_sample_point_from_geoseries():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (1,1), (0,1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    assert isinstance(facility.sample_point_from_polygon(gdf.geometry[0]), Point)


def test_sample_point_from_geoseries_invalid():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (0,1), (1,1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    assert isinstance(facility.sample_point_from_polygon(gdf.geometry[0]), Point)


def test_sample_point_from_geoseries_impatient():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (0,0)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    assert facility.sample_point_from_polygon(gdf.geometry[0], patience=0) is None


def test_random_point_from_geoseries():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (1,1), (0,1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    assert isinstance(facility.random_point(0, gdf.geometry), Point)


def test_random_point_from_geodataframe():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (1,1), (0,1)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    assert isinstance(facility.random_point(0, gdf), Point)


def test_random_point_from_geoseries_impatient():
    df = pd.DataFrame({1:[1,2,3], 2: [4,5,6]})
    poly = Polygon(((0,0), (1,0), (0,0)))
    gdf = gp.GeoDataFrame(df, geometry=[poly]*3)
    with pytest.raises(TimeoutError):
        facility.random_point(0, gdf.geometry, fail=True, patience=0)