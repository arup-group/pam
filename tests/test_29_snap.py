import os

import geopandas as gp
import pytest
from pam.operations.snap import run_facility_link_snapping, snap_facilities_to_network
from pam.read import read_matsim


def test_add_snapping_adds_link_attribute(population_heh):
    network = gp.read_file(pytest.test_data_dir / "test_link_geometry.geojson")
    for _, _, person in population_heh.people():
        for act in person.activities:
            assert act.location.link is None

    snap_facilities_to_network(population=population_heh, network=network)
    for _, _, person in population_heh.people():
        for act in person.activities:
            assert act.location.link is not None

            # check that the link is indeed the nearest one
            link_distance = (
                network.set_index("id")
                .loc[act.location.link, "geometry"]
                .distance(act.location.loc)
            )
            min_distance = network.distance(act.location.loc).min()
            assert link_distance == min_distance


def test_links_resnapped(tmpdir):
    path_out = os.path.join(tmpdir, "pop_snapped.xml")
    run_facility_link_snapping(
        path_population_in=pytest.test_data_dir / "1.plans.xml",
        path_population_out=path_out,
        path_network_geometry=pytest.test_data_dir / "test_link_geometry.geojson",
    )
    assert os.path.exists(path_out)
    pop_snapped = read_matsim(path_out)
    for _, _, person in pop_snapped.people():
        for act in person.activities:
            assert "link-" in act.location.link
