""" Methods for snapping elements to the network or facilities. """

from pathlib import Path

import geopandas as gp

from pam.core import Population
from pam.read import read_matsim
from pam.write import write_matsim


def snap_facilities_to_network(
    population: Population, network: gp.GeoDataFrame, link_id_field: str = "id"
) -> None:
    """Snaps activity facilities to a network geometry (in-place).

    Args:
        population (Population): A PAM population.
        network (gp.GeoDataFrame): A network geometry shapefile.
        link_id_field (str, optional): The link ID field to use in the network shapefile. Defaults to "id".
    """
    link_ids = network[link_id_field]
    for _, _, person in population.people():
        for act in person.activities:
            link_id = link_ids[network.distance(act.location.loc).argmin()]
            act.location.link = link_id


def run_facility_link_snapping(
    path_population_in: str,
    path_population_out: str,
    path_network_geometry: str,
    link_id_field: str = "id",
) -> None:
    """Reads a population, snaps activity facilities to a network geometry, and saves the results.

    Args:
        path_population_in (str): Path to a PAM population.
        path_population_out (str): The path to save the output population.
        path_network_geometry (str): Path to the network geometry file.
        link_id_field (str, optional): The link ID field to use in the network shapefile. Defaults to "id".
    """
    population = read_matsim(path_population_in)
    if ".parquet" in Path(path_network_geometry).suffixes:
        network = gp.read_parquet(path_network_geometry)
    else:
        network = gp.read_file(path_network_geometry)
    snap_facilities_to_network(population=population, network=network, link_id_field=link_id_field)
    write_matsim(population=population, plans_path=path_population_out)
