from datetime import datetime
import numpy as np
import gzip
from lxml import etree
from io import BytesIO
import os
from shapely.geometry import Point, LineString
from s2sphere import CellId


def parse_time(time):
    if isinstance(time, int) or isinstance(time, np.int64):
        return minutes_to_datetime(time)
    if isinstance(time, str):
        return datetime_string_to_datetime(time)
    raise UserWarning(f"Cannot parse {time} of type {type(time)} that is not int (assuming minutes) or str (%Y-%m-%d %H:%M:%S)")


def minutes_to_datetime(minutes: int):
    """
    Convert minutes to datetime
    :param minutes: int
    :return: datetime
    """
    days, remainder = divmod(minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return datetime(1900, 1, 1+days, hours, minutes)


def datetime_string_to_datetime(string: str):
    """
    Convert datetime formatted string to datetime
    :param string: str "%Y-%m-%d %H:%M:%S"
    :return: datetime
    """
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


def datetime_to_matsim_time(dt):
    """
    Convert datetime to matsim format time (08:27:33)
    """
    return dt.strftime("%H:%M:%S")


def matsim_time_to_datetime(string):
    """
    Convert matsim format time (08:27:33) to datetime.
    """
    return datetime.strptime(string, "%H:%M:%S")


def timedelta_to_matsim_time(td):
    """
    Convert datetime timedelta object to matsim string format (00:00:00)
    """
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

      
def dt_to_s(dt):
    """
    Convert datetime to seconds since start of day.
    """
    return (((dt.hour * 60) + dt.minute) * 60) + dt.second


def td_to_s(td):
    """
    Convert timedelta to seconds since start of day.
    """
    # if not td.seconds and td.days:
    #     return 24*60*60
    return td.seconds


def get_linestring(from_point, to_point):
    """
    Makes a shapely.geometry.LineString out of two points
    :param from_point: shapely.geometry.Point or s2sphere.CellId
    :param to_point: shapely.geometry.Point or s2sphere.CellId
    :return:
    """
    if all(isinstance(p, CellId) for p in [from_point, to_point]):
        from_point = from_point.to_lat_lng()
        from_point = Point(from_point.lng().degrees, from_point.lat().degrees)
        to_point = to_point.to_lat_lng()
        to_point = Point(to_point.lng().degrees, to_point.lat().degrees)

    if not all(isinstance(p, Point) for p in [from_point, to_point]):
        raise TypeError(f'You need to pass points of type {type(Point)} or {type(CellId)}.'
                        f'Types passed: type(from_point)={type(from_point)} and type(to_point)={type(to_point)}')
    return LineString([from_point, to_point])


def get_elems(path, tag):
    """
    Wrapper for unzipping and dealing with xml namespaces
    :param path: xml path string
    :param tag: The tag type to extract , e.g. 'link'
    :return: Generator of elements
    """
    target = try_unzip(path)
    tag = get_tag(target, tag)
    target = try_unzip(path)  # need to repeat :(
    return parse_elems(target, tag)


def parse_elems(target, tag):
    """
    Traverse the given XML tree, retrieving the elements of the specified tag.
    :param target: Target xml, either BytesIO object or string path
    :param tag: The tag type to extract , e.g. 'link'
    :return: Generator of elements
    """
    doc = etree.iterparse(target, tag=tag)
    for _, element in doc:
        yield element
        element.clear()
        del element.getparent()[0]
    del doc


def try_unzip(path):
    """
    Attempts to unzip xml at given path, if fails, returns path
    :param path: xml path string
    :return: either BytesIO object or string path
    """
    try:
        with gzip.open(path) as unzipped:
            xml = unzipped.read()
            target = BytesIO(xml)
            return target
    except OSError:
        return path


def get_tag(target, tag):
    """
    Check for namespace declaration. If they exists return tag string
    with namespace [''] ie {namespaces['']}tag. If no namespaces declared
    return original tag
    TODO Not working with iterparse, generated elem also have ns which is dealt with later
    """
    nsmap = {}
    doc = etree.iterparse(target, events=('end', 'start-ns',))
    count = 0
    for event, element in doc:
        count += 1
        if event == 'start-ns':
            nsmap[element[0]] = element[1]
        if count == 10:  # assume namespace declared at top so can break early
            del doc
            break
    if not nsmap:
        return tag
    else:
        tag = '{' + nsmap[''] + '}' + tag
        return tag


def strip_namespace(elem):
    """
    Strips namespaces from given xml element
    :param elem: xml element
    :return: xml element
    """
    if elem.tag.startswith("{"):
        elem.tag = elem.tag.split('}', 1)[1]  # strip namespace
    for k in elem.attrib.keys():
        if k.startswith("{"):
            k2 = k.split('}', 1)[1]
            elem.attrib[k2] = elem.attrib[k]
            del elem.attrib[k]
    for child in elem:
        strip_namespace(child)


def write_xml(population_xml, location, matsim_DOCTYPE, matsim_filename):

    create_local_dir(os.path.dirname(location))

    content = xml_content(
        population_xml,
        matsim_DOCTYPE=matsim_DOCTYPE,
        matsim_filename=matsim_filename
    )

    if is_gzip(location):
        file = gzip.open(location, "w")
    else:
        file = open(location, "wb")

    file.write(content)
    file.close()


def is_xml(location):
    return location.lower().endswith(".xml")


def is_gzip(location):
    return location.lower().endswith(".gz") or location.lower().endswith(".gzip")


def create_local_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def xml_tree(content):
    tree = etree.tostring(content,
                       pretty_print=True,
                       xml_declaration=False,
                       encoding='UTF-8')
    return tree


def xml_content(content, matsim_DOCTYPE, matsim_filename):
    xml_version = b'<?xml version="1.0" encoding="UTF-8"?>'
    doc_type = f'<!DOCTYPE {matsim_DOCTYPE} SYSTEM "http://matsim.org/files/dtd/{matsim_filename}.dtd">'.encode()
    tree = xml_tree(content)
    return xml_version+doc_type+tree


def safe_strptime(s):
    """
    safely parse string into datatime, can cope with time strings in format hh:mm:ss
    if hh > 23 then adds a day
    """
    if int(s.split(':')[0]) > 23:
        days, hours = divmod(int(s.split(':')[0]),24)
        string = f"{days+1}-{hours:02d}" + s[-6:]
        return datetime.strptime(string, '%d-%H:%M:%S')
    return datetime.strptime(s, '%H:%M:%S')


def timedelta_to_hours(td):
    return td.total_seconds() / 3600


def matsim_duration_to_hours(mt):
    mt = mt.split(":")
    return int(mt.pop()) / 3600 + int(mt.pop()) / 60 + int(mt.pop())
