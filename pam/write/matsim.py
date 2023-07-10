from __future__ import annotations
import os
from datetime import datetime
import logging
from pathlib import Path
from lxml import etree as et
from typing import Optional, Union

from pam.activity import Plan, Activity, Leg
from pam.utils import create_crs_attribute, datetime_to_matsim_time as dttm
from pam.utils import timedelta_to_matsim_time as tdtm
from pam.utils import create_local_dir, is_gzip, DEFAULT_GZIP_COMPRESSION
from pam.vehicles import Vehicle


def write_matsim(
    population,
    plans_path: Union[Path, str],
    attributes_path: Union[Path, str, None] = None,
    vehs_path: Union[Path, str, None] = None,
    evs_path: Union[Path, str, None] = None,
    version: int = None,
    comment: Optional[str] = None,
    household_key: Optional[str] = "hid",
    keep_non_selected: bool = False,
    coordinate_reference_system: str = None,
) -> None:
    """
    Write a core population to matsim population v6 xml format.
    Note that this requires activity locs to be set (shapely.geometry.Point).

    :param population: core.Population, population to be writen to disk
    :param plans_path: {str, Path}, output path (.xml or .xml.gz)
    :param attributes_path: legacy parameter, does not have an effect
    :param vehs_path: {str, Path, None}, default None, path to output vehicle file
    :param evs_path: {str, Path, None}, default None, path to output ev file
    :param version: legacy parameter, does not have an effect
    :param comment: {str, None}, default None, optionally add a comment string to the xml outputs
    :param household_key: {str, None}, optionally add household id to person attributes, default 'hid'
    :param keep_non_selected: bool, default False
    :param coordinate_reference_system: {str, None}, default None, optionally add CRS attribute to xml outputs
    :return: None
    """

    if version is not None:
        logging.warning('parameter "version" is no longer supported by write_matsim()')
    if attributes_path is not None:
        logging.warning('parameter "attributes_path" is no longer supported by write_matsim()')
    if vehs_path is None and evs_path is not None:
        raise UserWarning("You must provide a vehs_path in addition to evs_path.")

    write_matsim_population_v6(
        population=population,
        path=plans_path,
        comment=comment,
        household_key=household_key,
        keep_non_selected=keep_non_selected,
        coordinate_reference_system=coordinate_reference_system,
    )

    # write vehicles
    if vehs_path is not None:
        logging.info("Building population vehicles output.")
        # rebuild vehicles output from population
        population.rebuild_vehicles_manager()
        population.vehicles_manager.to_xml(vehs_path, evs_path)


class Writer:
    """
    Context Manager for writing to xml. Designed to handle the boilerplate xml.
    For example:
    `with pam.write.matsim.Writer(PATH) as writer:
        for hid, household in population:
            writer.add_hh(household)
    `
    For example:
    `with pam.write.matsim.Writer(OUT_PATH) as writer:
        for person in pam.read.matsim.stream_matsim_persons(IN_PATH):
            pam.samplers.time.apply_jitter_to_plan(person.plan)
            writer.add_person(household)
    `
    """

    def __init__(
        self,
        path: str,
        household_key: Optional[str] = "hid",
        comment: Optional[str] = None,
        keep_non_selected: bool = False,
        coordinate_reference_system: str = None,
    ) -> None:
        if os.path.dirname(path):
            create_local_dir(os.path.dirname(path))
        self.path = path
        self.household_key = household_key
        self.comment = comment
        self.keep_non_selected = keep_non_selected
        self.coordinate_reference_system = coordinate_reference_system
        self.compression = DEFAULT_GZIP_COMPRESSION if is_gzip(path) else 0
        self.xmlfile = None
        self.writer = None
        self.population_writer = None

    def __enter__(self) -> Writer:
        self.xmlfile = et.xmlfile(self.path, encoding="utf-8", compression=self.compression)
        self.writer = self.xmlfile.__enter__()  # enter into lxml file writer
        self.writer.write_declaration()
        self.writer.write_doctype('<!DOCTYPE population SYSTEM "http://matsim.org/files/dtd/population_v6.dtd">')
        if self.comment:
            self.writer.write(et.Comment(self.comment), pretty_print=True)
        self.writer.write(et.Comment(f"Created {datetime.today()}"), pretty_print=True)

        self.population_writer = self.writer.element("population")
        self.population_writer.__enter__()  # enter into lxml element writer
        if self.coordinate_reference_system is not None:
            self.writer.write(
                create_crs_attribute(self.coordinate_reference_system),
                pretty_print=True,
            )
        return self

    def add_hh(self, household) -> None:
        for _, person in household:
            if self.household_key is not None:
                person.attributes[self.household_key] = household.hid  # force add hid as an attribute
            self.add_person(person)

    def add_person(self, person) -> None:
        e = create_person_element(person.pid, person, self.keep_non_selected)
        self.writer.write(e, pretty_print=True)

    def __exit__(self, exc_type, exc_value, traceback):
        self.population_writer.__exit__(exc_type, exc_value, traceback)
        self.xmlfile.__exit__(exc_type, exc_value, traceback)


def write_matsim_population_v6(
    population,
    path: str,
    household_key: Optional[str] = "hid",
    comment: Optional[str] = None,
    keep_non_selected: bool = False,
    coordinate_reference_system: str = None,
) -> None:
    """
    Write matsim population v6 xml (persons plans and attributes combined).
    :param population: core.Population, population to be writen to disk
    :param path: str, output path (.xml or .xml.gz)
    :param comment: {str, None}, default None, optionally add a comment string to the xml outputs
    :param household_key: {str, None}, default 'hid'
    :param keep_non_selected: bool, default False
    """

    with Writer(
        path=path,
        household_key=household_key,
        comment=comment,
        keep_non_selected=keep_non_selected,
        coordinate_reference_system=coordinate_reference_system,
    ) as writer:
        for _, household in population:
            writer.add_hh(household)


def create_person_element(pid, person, keep_non_selected: bool = False):
    person_xml = et.Element("person", {"id": str(pid)})

    attributes = et.SubElement(person_xml, "attributes", {})
    if person.vehicles:
        attribute = et.SubElement(
            attributes,
            "attribute",
            {"class": "org.matsim.vehicles.PersonVehicles", "name": str("vehicles")},
        )
        attribute.text = str({k: v.vid for k, v in person.vehicles.items()}).replace("'", '"')

    for k, v in person.attributes.items():
        add_attribute(attributes, k, v)

    write_plan(
        person_xml,
        person.plan,
        selected=True,
    )
    if keep_non_selected:
        for plan in person.plans_non_selected:
            write_plan(
                person_xml,
                plan,
                selected=False,
            )
    return person_xml


def write_plan(
    person_xml: et.SubElement,
    plan: Plan,
    selected: Optional[bool] = None,
):
    plan_attributes = {}
    if selected is not None:
        plan_attributes["selected"] = {True: "yes", False: "no"}[selected]
    if plan.score is not None:
        plan_attributes["score"] = str(plan.score)

    plan_xml = et.SubElement(person_xml, "plan", plan_attributes)
    for component in plan:
        if isinstance(component, Activity):
            component.validate_matsim()
            act_data = {
                "type": component.act,
            }
            if component.start_time is not None:
                act_data["start_time"] = dttm(component.start_time)
            if component.end_time is not None:
                act_data["end_time"] = dttm(component.end_time)
            if component.location.link is not None:
                act_data["link"] = str(component.location.link)
            if component.location.x is not None:
                act_data["x"] = str(component.location.x)
            if component.location.y is not None:
                act_data["y"] = str(component.location.y)
            et.SubElement(plan_xml, "activity", act_data)

        if isinstance(component, Leg):
            leg = et.SubElement(
                plan_xml,
                "leg",
                {"mode": component.mode, "trav_time": tdtm(component.duration)},
            )

            if component.attributes:
                attributes = et.SubElement(leg, "attributes")
                for k, v in component.attributes.items():
                    if k == "enterVehicleTime":  # todo make something more robust for future 'special' classes
                        attribute = et.SubElement(
                            attributes,
                            "attribute",
                            {"class": "java.lang.Double", "name": str(k)},
                        )
                        attribute.text = str(v)
                    else:
                        add_attribute(attributes, k, v)

            if component.route.exists:
                leg.append(component.route.xml)


def add_attribute(attributes, k, v):
    if isinstance(v, str):
        attribute = et.SubElement(attributes, "attribute", {"class": "java.lang.String", "name": str(k)})
        attribute.text = str(v)
    elif isinstance(v, bool):
        attribute = et.SubElement(attributes, "attribute", {"class": "java.lang.Boolean", "name": str(k)})
        attribute.text = str(v)
    elif isinstance(v, int):
        attribute = et.SubElement(attributes, "attribute", {"class": "java.lang.Integer", "name": str(k)})
        attribute.text = str(v)
    elif isinstance(v, float):
        attribute = et.SubElement(attributes, "attribute", {"class": "java.lang.Double", "name": str(k)})
        attribute.text = str(v)
    elif k == "vehicles":
        attribute = et.SubElement(
            attributes,
            "attribute",
            {"class": "org.matsim.vehicles.PersonVehicles", "name": str("vehicles")},
        )
        attribute.text = str(v).replace("'", '"')
    else:
        attribute = et.SubElement(attributes, "attribute", {"class": "java.lang.String", "name": str(k)})
        attribute.text = str(v)


def object_attributes_dtd():
    dtd_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "dtd",
            "objectattributes_v1.dtd",
        )
    )
    return et.DTD(dtd_path)


def population_v6_dtd():
    dtd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "dtd", "population_v6.dtd"))
    return et.DTD(dtd_path)
