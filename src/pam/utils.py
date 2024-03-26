import gzip
import os
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Generator, Union

import numpy as np
from lxml import etree as et
from s2sphere import CellId
from shapely.geometry import LineString, Point

from pam.variables import START_OF_DAY

# according to gzip manpage
DEFAULT_GZIP_COMPRESSION = 6


def parse_time(time: Union[int, str]) -> datetime:
    """Generic parse time into datetime.

    Integers are assumed to be minutes.
    Strings are assumed to be datetime formatted as (%Y-%m-%d %H:%M:%S).

    Args:
        time (Union[int, str]): time

    Raises:
        UserWarning: raised if wrong types provided

    Returns:
        datetime: datetime
    """

    if isinstance(time, (int, np.integer)) and not isinstance(time, bool):
        return minutes_to_datetime(time)
    elif isinstance(time, str):
        return datetime_string_to_datetime(time)
    else:
        raise TypeError(
            f"Cannot parse {time} of type {type(time)} that is not int (assuming minutes) or str (%Y-%m-%d %H:%M:%S)"
        )


def minutes_to_datetime(minutes: Union[int, float]) -> datetime:
    """Convert minutes to datetime.

    Args:
        minutes (Union[int, float]): minutes.

    Returns:
        datetime: datetime
    """
    return START_OF_DAY + minutes_to_timedelta(minutes)


def datetime_string_to_datetime(string: str) -> datetime:
    """Convert datetime formatted string to datetime.

    Args:
        string (str): time string formatted "%Y-%m-%d %H:%M:%S".

    Returns:
        datetime: datetime
    """
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


def minutes_to_timedelta(minutes: Union[int, float]) -> timedelta:
    """Convert minutes to timedelta.

    Args:
        minutes (Union[int, float]): minutes.

    Returns:
        timedelta: timedelta
    """
    return timedelta(minutes=float(minutes))


def datetime_to_matsim_time(dt: datetime) -> str:
    """Convert datetime to matsim format time (`hh:mm:ss`).

    Datetimes beyond 1 day will be converted to hours, eg 25:00:00, for 1am the next day.

    Args:
        dt (datetime): datetime

    Returns:
        str: MATSim time format (`hh:mm:ss`)
    """
    return timedelta_to_matsim_time(dt - START_OF_DAY)


def timedelta_to_matsim_time(td: timedelta) -> str:
    """Convert datetime timedelta object to matsim string format (`hh:mm:ss`).

    Args:
        td (timedelta): timedelta

    Returns:
        str: MATSim time string (`hh:mm:ss`)
    """
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def matsim_time_to_datetime(string: str) -> datetime:
    """Convert matsim format time (`hh:mm:ss`) to datetime.

    Can read MATSim times for any day of a simulation (ie 25:00:00 is read as 01:00:00 of the next day).

    Args:
        string (str): MATSim time from start of the simulation (%H:%M:%S)

    Returns:
        datetime: datetime
    """
    return safe_strptime(string)


def dt_to_s(dt: datetime) -> int:
    """Convert datetime to seconds since start of day.

    Args:
        dt (datetime): datetime

    Returns:
        int: seconds as integer
    """
    return (((dt.hour * 60) + dt.minute) * 60) + dt.second


def td_to_s(td: timedelta) -> int:
    """Convert timedelta to seconds since start of day.

    Args:
        td (timedelta): timedelta

    Returns:
        int: seconds as integer
    """
    return (td.days * 86400) + td.seconds


def safe_strptime(mt: str) -> datetime:
    """Safely parse string into datetime.

    Can cope with time strings in format `hh:mm:ss` if hh > 24 then adds a day.

    Args:
        mt (str): MATSim time string (`hh:mm:ss` or `hh:mm`)

    Returns:
        datetime: datetime
    """
    return START_OF_DAY + safe_strpdelta(mt)


def safe_strpdelta(mt: str) -> timedelta:
    """Parse string into timedelta.

    Can cope with time strings in format `hh:mm:ss` or `hh:mm`.

    Args:
        mt (str): MATSim time string (`hh:mm:ss` or `hh:mm`)

    Raises:
        UserWarning: Incorrect formatted input

    Returns:
        timedelta: timedelta
    """
    units = mt.split(":")
    if len(units) == 3:
        h, m, s = mt.split(":")
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))
    if len(units) == 2:
        h, m = mt.split(":")
        return timedelta(hours=int(h), minutes=int(m))
    raise UserWarning(f"Unrecognised timedelta format: {mt}")


def timedelta_to_hours(td: timedelta) -> float:
    """Timedelta to hours.

    Args:
        td (timedelta): timedelta

    Returns:
        float: hours as float
    """
    return td.total_seconds() / 3600


def matsim_duration_to_hours(mt: str) -> float:
    """Turn MATSim time string (`hh:mm:ss` or `hh:mm`) into hours.

    Args:
        mt (str): MATSim time string (`hh:mm:ss` or `hh:mm`)

    Raises:
        UserWarning: Incorrect formatted input

    Returns:
        int: hours as integer
    """
    td = safe_strpdelta(mt)
    return timedelta_to_hours(td)


def get_linestring(from_point: Union[Point, CellId], to_point: Union[Point, CellId]) -> LineString:
    """Makes a shapely.geometry.LineString out of two points.

    Args:
        from_point (Union[Point, CellId]): shapely.geometry.Point or s2sphere.CellId
        to_point (Union[Point, CellId])): shapely.geometry.Point or s2sphere.CellId

    Raises:
        TypeError: Failure to parse inputs

    Returns:
        LineString: LineString
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


def get_elems(path: Union[str, Path], tag: str) -> Generator:
    """Wrapper for unzipping and dealing with xml namespaces

    Args:
        path (Union[str, Path]): xml path
        tag (str): The tag type to extract , e.g. 'link'

    Yields:
        Generator:  Generator of elements
    """
    target = try_unzip(path)
    tag = get_tag(target, tag)
    target = try_unzip(path)  # need to repeat :(
    return parse_elems(target, tag)


def parse_elems(target: Union[BytesIO, str, Path], tag: str) -> Generator:
    """Traverse the given XML tree, retrieving the elements of the specified tag.

    Args:
        target (Union[BytesIO, str, Path]): Target xml, either BytesIO object or string path
        tag (str): The tag type to extract , e.g. 'link'

    Yields:
        Generator: Generator of elements.
    """
    doc = et.iterparse(target, tag=tag)
    for _, element in doc:
        yield element
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]
    del doc


def try_unzip(path: Union[str, Path]) -> Union[BytesIO, str, Path]:
    """Attempts to unzip xml at given path, if fails, returns path

    Args:
        path (Union[str, Path]): xml path.

    Returns:
        Union[BytesIO, str, Path]: BytesIO object or path if already unzipped.
    """
    try:
        with gzip.open(path) as unzipped:
            xml = unzipped.read()
            target = BytesIO(xml)
            return target
    except OSError:
        return path


def get_tag(target: Union[BytesIO, str, Path], tag: str) -> str:
    """Check for namespace declaration.

    If they exists return tag string with namespace [''] ie {namespaces['']}tag.
    If no namespaces declared return original tag.

    TODO: Not working with iterparse, generated elem also have ns which is dealt with later.

    Args:
        target (Union[BytesIO, str, Path]): Target xml, either BytesIO object or path.
        tag (str): The tag type to extract , e.g. 'link'.

    Returns:
        str: tag.
    """
    nsmap = {}
    doc = et.iterparse(target, events=("end", "start-ns"))
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


def strip_namespace(elem: et.Element):
    """Strips namespaces from given xml element

    Args:
        elem (et.Element): xml element
    """
    if elem.tag.startswith("{"):
        # strip namespace
        elem.tag = elem.tag.split("}", 1)[1]
    for k in elem.attrib.keys():
        if k.startswith("{"):
            k2 = k.split("}", 1)[1]
            elem.attrib[k2] = elem.attrib[k]
            del elem.attrib[k]
    for child in elem:
        strip_namespace(child)


def create_crs_attribute(coordinate_reference_system: str) -> et.Element:
    """Create a CRS attribute as expected by MATSim's ProjectionUtils.getCRS.

    Args:
        coordinate_reference_system (str): coordinate reference system.

    Returns:
        et.Element: CRS attribute as xml element
    """
    attributes_element = et.Element("attributes")
    crs_attribute = et.SubElement(
        attributes_element,
        "attribute",
        {"class": "java.lang.String", "name": "coordinateReferenceSystem"},
    )
    crs_attribute.text = str(coordinate_reference_system)
    return attributes_element


def is_xml(location: Union[str, Path]) -> bool:
    """Checks if file is xml based on extension.

    Args:
        location (Union[str, Path]): file path.

    Returns:
        bool: is xml?
    """
    return Path(location).suffix.lower() == ".xml"


def is_gzip(location: Union[str, Path]) -> bool:
    """Checks if file is gzipped based on extension.

    Args:
        location (Union[str, Path]): file path

    Returns:
        bool: is gzipped?
    """
    suffix = Path(location).suffix.lower()
    return suffix == ".gz" or suffix == ".gzip"


def create_local_dir(directory: Union[str, Path]):
    """Safely create new directory.
    TODO this can be replaced with pathlib I think

    Args:
        directory (Union[str, Path]): new directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def xml_tree(content: et.Element) -> str:
    """Return pretty formatted string of xml tree.

    Args:
        content (et.Element): xml

    Returns:
        str: pretty string of xml
    """
    tree = et.tostring(content, pretty_print=True, xml_declaration=False, encoding="UTF-8")
    return tree
