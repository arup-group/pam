from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pam.core import Population

import geopandas as gp
import pandas as pd
from shapely.geometry import LineString

from pam.activity import Activity, Leg
from pam.utils import create_local_dir


def to_csv(
    population: Population, dir: str, crs: Optional[str] = None, to_crs: Optional[str] = "EPSG:4326"
) -> None:
    """Write a population to disk as tabular data in csv format.

    Outputs saved to file are:
    - households.csv: household ids and attributes
    - people.csv: agent ids and attributes
    - legs.csv: activity plan trip records
    - activities.csv: corresponding plan activities
    If activity locs (shapely.Point) data is available then geojsons will also be written.

    Args:
      population (Population):
      dir (str): path to output directory
      crs (Optional[str]): population coordinate system (generally we use local grid systems). Defaults to None.
      to_crs (Optional[str]): output crs, defaults for use in kepler. Defaults to "EPSG:4326".

    """
    create_local_dir(dir)

    hhs = []
    people = []
    acts = []
    legs = []

    for hid, hh in population.households.items():
        hh_data = {"hid": hid, "freq": hh.freq, "hzone": hh.location.area}
        if isinstance(hh.attributes, dict):
            hh_data.update(hh.attributes)
        if hh.location.loc is not None:
            hh_data["geometry"] = hh.location.loc

        hhs.append(hh_data)

        for pid, person in hh.people.items():
            people_data = {"pid": pid, "hid": hid, "freq": person.freq, "hzone": hh.location.area}
            if isinstance(person.attributes, dict):
                people_data.update(person.attributes)
            if hh.location.loc is not None:
                people_data["geometry"] = hh.location.loc

            people.append(people_data)

            for seq, component in enumerate(person.plan):
                if isinstance(component, Leg):
                    leg_data = {
                        "pid": pid,
                        "hid": hid,
                        "freq": component.freq,
                        "ozone": component.start_location.area,
                        "dzone": component.end_location.area,
                        "purp": component.purp,
                        "origin activity": person.plan[seq - 1].act,
                        "destination activity": person.plan[seq + 1].act,
                        "mode": component.mode,
                        "seq": component.seq,
                        "tst": component.start_time,
                        "tet": component.end_time,
                        "duration": str(component.duration),
                    }
                    if (
                        component.start_location.loc is not None
                        and component.end_location.loc is not None
                    ):
                        leg_data["geometry"] = LineString(
                            (component.start_location.loc, component.end_location.loc)
                        )

                    legs.append(leg_data)

                if isinstance(component, Activity):
                    act_data = {
                        "pid": pid,
                        "hid": hid,
                        "freq": component.freq,
                        "activity": component.act,
                        "seq": component.seq,
                        "start time": component.start_time,
                        "end time": component.end_time,
                        "duration": str(component.duration),
                        "zone": component.location.area,
                    }
                    if component.location.loc is not None:
                        act_data["geometry"] = component.location.loc

                    acts.append(act_data)

    hhs = pd.DataFrame(hhs).set_index("hid")
    save_geojson(hhs, crs, to_crs, os.path.join(dir, "households.geojson"))
    save_csv(hhs, os.path.join(dir, "households.csv"))

    people = pd.DataFrame(people).set_index("pid")
    save_geojson(people, crs, to_crs, os.path.join(dir, "people.geojson"))
    save_csv(people, os.path.join(dir, "people.csv"))

    legs = pd.DataFrame(legs)
    save_geojson(legs, crs, to_crs, os.path.join(dir, "legs.geojson"))
    save_csv(legs, os.path.join(dir, "legs.csv"))

    acts = pd.DataFrame(acts)
    save_geojson(acts, crs, to_crs, os.path.join(dir, "activities.geojson"))
    save_csv(acts, os.path.join(dir, "activities.csv"))


def dump(
    population: Population, dir: str, crs: Optional[str] = None, to_crs: Optional[str] = "EPSG:4326"
) -> None:
    """Write a population to disk as tabular data in csv format.

    Outputs saved to file are:
    - households.csv: household ids and attributes
    - people.csv: agent ids and attributes
    - legs.csv: activity plan trip records
    - activities.csv: corresponding plan activities
    If activity locs (shapely.Point) data is available then geojsons will also be written.

    Args:
      population (Population):
      dir (str): path to output directory
      crs (Optional[str]): population coordinate system (generally we use local grid systems). Defaults to None.
      to_crs (Optional[str]): output crs, defaults for use in kepler. Defaults to "EPSG:4326".
    """
    to_csv(population=population, dir=dir, crs=crs, to_crs=to_crs)


def save_geojson(df, crs, to_crs, path):
    if "geometry" in df.columns:
        df = gp.GeoDataFrame(df, geometry="geometry")
        if crs is not None:
            df.crs = crs
            df.to_crs(to_crs, inplace=True)
        df.to_file(path, driver="GeoJSON")


def save_csv(df, path):
    """Write GeoDataFrame as csv by dropping geometry column."""
    if "geometry" in df.columns:
        df = df.drop("geometry", axis=1)
    df.to_csv(path)


def write_population_csvs(
    list_of_populations: list[Population],
    dir: str,
    crs: Optional[str] = None,
    to_crs: Optional[str] = "EPSG:4326",
) -> None:
    """Write a list of populations to disk as tabular data in csv format.

    Outputs saved to file are:
    - populations.csv: summary of populations
    - households.csv: household ids and attributes
    - people.csv: agent ids and attributes
    - legs.csv: activity plan trip records
    - activities.csv: corresponding plan activities
    If activity locs (shapely.Point) data is available then geojsons will also be written.

    Args:
      list_of_populations (list[Population]):
      dir (str): path to output directory
      crs (Optional[str]): population coordinate system (generally we use local grid systems). Defaults to None.
      to_crs (Optional[str]): output crs, defaults for use in kepler. Defaults to "EPSG:4326".
    """
    create_local_dir(dir)

    populations = []
    for idx, population in enumerate(list_of_populations):
        if population.name is None:
            population.name = idx
        populations.append({"population_id": idx, "population_name": population.name})
        to_csv(
            population=population, dir=os.path.join(dir, population.name), crs=crs, to_crs=to_crs
        )

    pd.DataFrame(populations).to_csv(os.path.join(dir, "populations.csv"), index=False)
