import pytest
from pam.samplers import spatial

geojson_path = pytest.test_data_dir / "test_geometry.geojson"


@pytest.fixture
def geo_sampler():
    return spatial.GeometryRandomSampler(
        geo_df_file=geojson_path, geometry_name_column="NAME", default_region="Croydon"
    )


def test_constructor_throws_exception_for_bad_default_region():
    with pytest.raises(KeyError):
        spatial.GeometryRandomSampler(
            geo_df_file=geojson_path, geometry_name_column="NAME", default_region="non_region"
        )


def test_sample_point_valid_region(geo_sampler):
    geo_id = geo_sampler.geo_df_loc_lookup["Croydon"]
    geom = geo_sampler.geo_df.geometry.loc[geo_id]

    point = geo_sampler.sample_point("Croydon")

    assert point.within(geom)


def test_sample_point_fallback_default_region(geo_sampler):
    geo_id = geo_sampler.geo_df_loc_lookup["Croydon"]
    default_geom = geo_sampler.geo_df.geometry.loc[geo_id]

    point = geo_sampler.sample_point("non_region")

    assert point.within(default_geom)


def test_sample_point_patience_exhausted(geo_sampler):
    with pytest.raises(RuntimeWarning):
        geo_sampler.sample_point("dummy_region", patience=0)
