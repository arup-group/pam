import gzip
import os
from collections.abc import Iterator
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Union

import numpy as np
from lxml import etree
from lxml import etree as et
from s2sphere import CellId
from shapely.geometry import LineString, Point

from pam.variables import START_OF_DAY

# according to gzip manpage
DEFAULT_GZIP_COMPRESSION = 6


def parse_time(time):
    if isinstance(time, int) or isinstance(time, np.int64):
        return minutes_to_datetime(time)
    if isinstance(time, str):
        return datetime_string_to_datetime(time)
    raise UserWarning(
        f"Cannot parse {time} of type {type(time)} that is not int (assuming minutes) or str (%Y-%m-%d %H:%M:%S)"
    )


def minutes_to_datetime(minutes: int) -> datetime:
    """Convert minutes to datetime

    Args:
      minutes (int):

    Returns:
      datetime:

    """
    days, remainder = divmod(minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return datetime(1900, 1, 1 + days, hours, minutes)


def minutes_to_timedelta(minutes: int) -> timedelta:
    """Convert minutes to timedelta

    Args:
      minutes (int):

    Returns:
      timedelta:

    """
    return timedelta(minutes=minutes)


def datetime_string_to_datetime(string: str) -> datetime:
    """Convert datetime formatted string to datetime

    Args:
      string (str): Of the form "%Y-%m-%d %H:%M:%S".

    Returns:
      datetime:

    """
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


def datetime_to_matsim_time(dt: datetime) -> str:
    """Convert datetime to matsim format time (08:27:33).

    Datetimes beyond 1 day will be converted to hours, eg 25:00:00, for 1am the next day.

    Args:
      dt (datetime):

    Returns:
      str:

    """
    return timedelta_to_matsim_time(dt - START_OF_DAY)


def matsim_time_to_datetime(string: str) -> datetime:
    """Convert matsim format time (08:27:33) to datetime.
    Can read MATSim times for any day of a simulation (ie 25:00:00 is read as 01:00:00 of the next day).

    Args:
      string (str): Time from start of the simulation (%H:%M:%S)

    Returns:
      datetime:
    """
    return safe_strptime(string)


def timedelta_to_matsim_time(td: timedelta) -> str:
    """Convert datetime timedelta object to matsim string format (00:00:00).

    Args:
      td (timedelta):

    Returns:
      str:
    """
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def dt_to_s(dt: datetime) -> int:
    """Convert datetime to seconds since start of day.

    Args:
      dt (datetime):

    Returns:
      int:

    """
    return (((dt.hour * 60) + dt.minute) * 60) + dt.second


def td_to_s(td: timedelta) -> int:
    """Convert timedelta to seconds since start of day.

    Args:
      td (timedelta):

    Returns:
      int:

    """
    return (td.days * 86400) + td.seconds


def safe_strptime(mt: str) -> datetime:
    """Safely parse string into datetime.

    Can cope with time strings in format hh:mm:ss if hh > 23 then adds a day.

    Args:
      mt (str):

    Returns:
      datetime:

    """
    units = mt.split(":")
    if len(units) == 3:
        h, m, s = mt.split(":")
        return START_OF_DAY + timedelta(hours=int(h), minutes=int(m), seconds=int(s))
    if len(units) == 2:
        h, m = mt.split(":")
        return START_OF_DAY + timedelta(hours=int(h), minutes=int(m))
    raise UserWarning(f"Unrecognised time format: {mt}")


def safe_strpdelta(mt):
    """Parse string into timedelta, can cope with time strings in format hh:mm:ss or hh:mm"""
    units = mt.split(":")
    if len(units) == 3:
        h, m, s = mt.split(":")
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))
    if len(units) == 2:
        h, m = mt.split(":")
        return timedelta(hours=int(h), minutes=int(m))
    raise UserWarning(f"Unrecognised timedelta format: {mt}")


def timedelta_to_hours(td):
    return td.total_seconds() / 3600


def matsim_duration_to_hours(mt):
    mt = mt.split(":")
    return int(mt.pop()) / 3600 + int(mt.pop()) / 60 + int(mt.pop())


def get_linestring(from_point: Union[Point, CellId], to_point: Union[Point, CellId]) -> LineString:
    """Makes a shapely.geometry.LineString out of two points

    Args:
      from_point (Union[Point, CellId]):
      to_point (Union[Point, CellId]):

    Returns:
      LineString:
    """
    if all(isinstance(p, CellId) for p in [from_point, to_point]):
        from_point = from_point.to_lat_lng()
        from_point = Point(from_point.lng().degrees, from_point.lat().degrees)
        to_point = to_point.to_lat_lng()
        to_point = Point(to_point.lng().degrees, to_point.lat().degrees)

    if not all(isinstance(p, Point) for p in [from_point, to_point]):
        raise TypeError(
            f"You need to pass points of type {type(Point)} or {type(CellId)}."
            f"Types passed: type(from_point)={type(from_point)} and type(to_point)={type(to_point)}"
        )
    return LineString([from_point, to_point])


def get_elems(path: str, tag: str) -> Iterator[Any]:
    """Wrapper for unzipping and dealing with xml namespaces

    Args:
      path (str): xml path string
      tag (str): The tag type to extract , e.g. 'link'

    Returns:
      Iterator[Any]: Generator of elements.

    """
    target = try_unzip(path)
    tag = get_tag(target, tag)
    target = try_unzip(path)  # need to repeat :(
    return parse_elems(target, tag)


def parse_elems(target: Union[BytesIO, str], tag: str) -> Iterator[Any]:
    """Traverse the given XML tree, retrieving the elements of the specified tag.

    Args:
      target (Union[BytesIO, str]): Target xml.
      tag (str): The tag type to extract , e.g. 'link'.

    Returns:
      Iterator[Any]: Generator of elements.

    """
    doc = etree.iterparse(target, tag=tag)
    for _, element in doc:
        yield element
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]
    del doc


def try_unzip(path: str) -> Union[BytesIO, str]:
    """Attempts to unzip xml at given path, if fails, returns path

    Args:
      path (str): xml path string

    Returns:
      Union[BytesIO, str]:

    """
    try:
        with gzip.open(path) as unzipped:
            xml = unzipped.read()
            target = BytesIO(xml)
            return target
    except OSError:
        return path


def get_tag(target: Union[BytesIO, str], tag: str) -> str:
    """Check for namespace declaration.

    If they exists return tag string with namespace [''] ie {namespaces['']} tag. If no namespaces declared

    TODO: Not working with iterparse, generated elem also have ns which is dealt with later.

    Args:
      target (Union[BytesIO, str]):
      tag (str):

    Returns:
      str:

    """
    nsmap = {}
    doc = etree.iterparse(target, events=("end", "start-ns"))
    count = 0
    for event, element in doc:
        count += 1
        if event == "start-ns":
            nsmap[element[0]] = element[1]
        if count == 10:  # assume namespace declared at top so can break early
            del doc
            break
    if not nsmap:
        return tag
    else:
        tag = "{" + nsmap[""] + "}" + tag
        return tag


def strip_namespace(elem: str) -> str:
    """Strips namespaces from given xml element

    Args:
      elem (str): xml element

    Returns:
      str: xml element.

    """
    if elem.tag.startswith("{"):
        elem.tag = elem.tag.split("}", 1)[1]  # strip namespace
    for k in elem.attrib.keys():
        if k.startswith("{"):
            k2 = k.split("}", 1)[1]
            elem.attrib[k2] = elem.attrib[k]
            del elem.attrib[k]
    for child in elem:
        strip_namespace(child)


def create_crs_attribute(coordinate_reference_system: str) -> Any:
    """Create a CRS attribute as expected by MATSim's ProjectionUtils.getCRS.

    Args:
      coordinate_reference_system (str):

    Returns:
      Any:

    """
    attributes_element = et.Element("attributes")
    crs_attribute = et.SubElement(
        attributes_element,
        "attribute",
        {"class": "java.lang.String", "name": "coordinateReferenceSystem"},
    )
    crs_attribute.text = str(coordinate_reference_system)
    return attributes_element


def is_xml(location):
    return Path(location).suffix.lower() == ".xml"


def is_gzip(location):
    suffix = Path(location).suffix.lower()
    return suffix == ".gz" or suffix == ".gzip"


def create_local_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def xml_tree(content):
    tree = etree.tostring(content, pretty_print=True, xml_declaration=False, encoding="UTF-8")
    return tree
