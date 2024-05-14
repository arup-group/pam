import os
from pathlib import Path

import geopandas as gp
from pam.operations.snap import run_facility_link_snapping, snap_facilities_to_network
from pam.read import read_matsim

TEST_DATA_DIR = Path(__file__).parent / "test_data"


def test_add_snapping_adds_link_attribute(population_heh):
    network = gp.read_file(os.path.join(TEST_DATA_DIR, "test_link_geometry.geojson"))
    for _, _, person in population_heh.people():
        for act in person.activities:
            assert act.location.link is None

    snap_facilities_to_network(population=population_heh, network=network)
    for _, _, person in population_heh.people():
        for act in person.activities:
            assert act.location.link is not None


def test_links_resnapped(tmpdir):
    path_out = os.path.join(tmpdir, "pop_snapped.xml")
    run_facility_link_snapping(
        path_population_in=os.path.join(TEST_DATA_DIR, "1.plans.xml"),
        path_population_out=path_out,
        path_network_geometry=os.path.join(TEST_DATA_DIR, "test_link_geometry.geojson"),
    )
    assert os.path.exists(path_out)
    pop_snapped = read_matsim(path_out)
    for _, _, person in pop_snapped.people():
        for act in person.activities:
            assert "link-" in act.location.link
