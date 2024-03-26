from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import timedelta
from typing import Literal, Optional

from shapely.geometry import Point

import pam.activity as activity
import pam.core as core
import pam.utils as utils
from pam.activity import Route, RouteV11
from pam.variables import START_OF_DAY
from pam.vehicles import VehicleManager


def read_matsim(
    plans_path: str,
    attributes_path: Optional[str] = None,
    all_vehicles_path: Optional[str] = None,
    electric_vehicles_path: Optional[str] = None,
    weight: int = 100,
    version: Literal[11, 12] = 12,
    household_key: Optional[str] = None,
    simplify_pt_trips: bool = False,
    autocomplete: bool = True,
    crop: bool = False,
    keep_non_selected: bool = False,
    leg_attributes: bool = True,
    leg_route: bool = True,
) -> core.Population:
    """Load a MATSim format population into core population format.
    It is possible to maintain the unity of housholds using a household uid in
    the attributes input, i.e.:
    ``` xml
        <attribute class="java.lang.String" name="hid">hh_0001</attribute>
    ```.

    Args:
        plans_path (str): path to matsim format xml
        attributes_path (str, optional): path to matsim format xml. Defaults to None.
        all_vehicles_path (str, optional): path to matsim all_vehicles xml file. Defaults to None.
        electric_vehicles_path (str, optional): path to matsim electric_vehicles xml. Defaults to None.
        weight (int, optional): int. Defaults to 100.
        version (Literal[11, 12], optional): Defaults to 12.
        household_key (str, optional): Defaults to None.
        simplify_pt_trips (bool, optional): bool, simplify legs in multi-leg trips. Defaults to False.
        autocomplete (bool, optional): bool, fills missing leg and activity attributes. Defaults to True.
        crop (bool, optional): bool, crop plans that go beyond 24 hours. Defaults to False.
        keep_non_selected (bool, optional): Whether to parse non-selected plans (storing them in person.plans_non_selected). Defaults to False.
        leg_attributes (bool, optional): Parse leg attributes such as routing mode. Defaults to True.
        leg_route (bool, optional): Parse leg route. Defaults to True.

    Returns:
        core.Population:
    """
    logger = logging.getLogger(__name__)

    population = core.Population()

    if attributes_path is not None and version == 12:
        raise UserWarning(
            """
You have provided an attributes_path and enabled matsim version 12, but
v12 does not require an attributes input:
Either remove the attributes_path arg, or enable version 11.
"""
        )

    if version not in [11, 12]:
        raise UserWarning("Version must be set to 11 or 12.")

    if version == 11 and not attributes_path:
        logger.warning(
            """
You have specified version 11 and not supplied an attributes path, population will not
have attributes or be able to use a household attribute id. Check this is intended.
"""
        )

    if all_vehicles_path:
        logger.debug(f"Loading vehicles from {all_vehicles_path}")
        if electric_vehicles_path:
            logger.debug(f"Loading EVs from {electric_vehicles_path}")
        population._vehicles_manager.from_xml(all_vehicles_path, electric_vehicles_path)

    attributes = {}
    if attributes_path:
        logger.debug(f"Loading attributes from {attributes_path}")
        if (version == 12) and (attributes_path is not None):
            logger.warning(
                "It is not required to load attributes from a separate path after version 11."
            )
        attributes = load_attributes_map(attributes_path)

    for person in stream_matsim_persons(
        plans_path,
        attributes=attributes,
        vehicles_manager=population._vehicles_manager,
        weight=weight,
        version=version,
        simplify_pt_trips=simplify_pt_trips,
        autocomplete=autocomplete,
        crop=crop,
        keep_non_selected=keep_non_selected,
        leg_attributes=leg_attributes,
        leg_route=leg_route,
    ):
        # Check if using households, then update population accordingly.
        if household_key and person.attributes.get(household_key):  # using households
            if population.get(person.attributes.get(household_key)):  # existing household
                household = population.get(person.attributes.get(household_key))
                household.add(person)
            else:  # new household
                household = core.Household(person.attributes.get(household_key), freq=weight)
                household.add(person)
                population.add(household)
        else:  # not using households, create dummy household
            household = core.Household(person.pid, freq=weight)
            household.add(person)
            population.add(household)

    return population


def stream_matsim_persons(
    plans_path: str,
    attributes: dict = {},
    vehicles_manager: Optional[VehicleManager] = None,
    weight: int = 100,
    version: Literal[11, 12] = 12,
    simplify_pt_trips: bool = False,
    autocomplete: bool = True,
    crop: bool = False,
    keep_non_selected: bool = False,
    leg_attributes: bool = True,
    leg_route: bool = True,
) -> Iterator[core.Person]:
    """Stream a MATSim format population into core.Person objects.
    Expects agent attributes (and vehicles) to be supplied as optional dictionaries.
    This allows this function to support "version 11" plans.

    TODO: a v12 only method could also stream attributes and would use less memory

    Args:
        plans_path (str):
            path to matsim format xml
        attributes (dict, optional):
            map of person attributes, only required for v11. Defaults to {}.
        vehicles_manager (VehicleManager, optional):
            Population vehicles manager. Defaults to None.
        weight (int, optional):
            path to matsim electric_vehicles xml. Defaults to 100.
        version (Literal[11, 12], optional):
            Defaults to 12.
        simplify_pt_trips (bool, optional):
            simplify legs in multi-leg trips. Defaults to False.
        autocomplete (bool, optional):
            fills missing leg and activity attributes. Defaults to True.
        crop (bool, optional):
            crop plans that go beyond 24 hours. Defaults to False.
        keep_non_selected (bool, optional):
            Whether to parse non-selected plans (storing them in `person.plans_non_selected`). Defaults to False.
        leg_attributes (bool, optional):
            Parse leg attributes such as routing mode. Defaults to True.
        leg_route (bool, optional):
            Parse leg route. Defaults to True.

    Raises:
        UserWarning: `version` must be set to 11 or 12.

    Yields:
        Iterator[core.Person]:
    """
    if version not in [11, 12]:
        raise UserWarning("Version must be set to 11 or 12.")

    if vehicles_manager is None:
        vehicles_manager = VehicleManager()

    for person_xml in utils.get_elems(plans_path, "person"):
        if version == 11:
            person_id = person_xml.xpath("@id")[0]
            agent_attributes = attributes.get(person_id, {})
        else:
            person_id, agent_attributes = get_attributes_from_person(person_xml)

        # remove vehicle attribute from agent and create person vehicles dictionary
        person_vehs = {}
        if vehicles_manager.len():
            agent_vehs = agent_attributes.pop("vehicles", {})
            person_vehs = {mode: vehicles_manager.pop(vid) for mode, vid in agent_vehs.items()}

        person = core.Person(
            person_id, attributes=agent_attributes, freq=weight, vehicles=person_vehs
        )

        for plan_xml in person_xml:
            if plan_xml.get("selected") == "yes":
                person.plan = parse_matsim_plan(
                    plan_xml=plan_xml,
                    person_id=person_id,
                    version=version,
                    simplify_pt_trips=simplify_pt_trips,
                    crop=crop,
                    autocomplete=autocomplete,
                    leg_attributes=leg_attributes,
                    leg_route=leg_route,
                )
            elif keep_non_selected and plan_xml.get("selected") == "no":
                person.plans_non_selected.append(
                    parse_matsim_plan(
                        plan_xml=plan_xml,
                        person_id=person_id,
                        version=version,
                        simplify_pt_trips=simplify_pt_trips,
                        crop=crop,
                        autocomplete=autocomplete,
                        leg_attributes=leg_attributes,
                        leg_route=leg_route,
                    )
                )
        yield person


def parse_matsim_plan(
    plan_xml,
    person_id: str,
    version: int,
    simplify_pt_trips: bool,
    crop: bool,
    autocomplete: bool,
    leg_attributes: bool = True,
    leg_route: bool = True,
) -> activity.Plan:
    """Parse a MATSim plan."""
    logger = logging.getLogger(__name__)
    act_seq = 0
    leg_seq = 0
    arrival_dt = START_OF_DAY
    departure_dt = None
    plan = activity.Plan()

    for stage in plan_xml:
        """
        Loop through stages incrementing time and extracting attributes.
        """
        if stage.tag in ["act", "activity"]:
            act_seq += 1
            act_type = stage.get("type")

            loc = None
            x, y = stage.get("x"), stage.get("y")
            if x and y:
                loc = Point(int(float(x)), int(float(y)))

            if act_type == "pt interaction":
                departure = stage.get("end_time")
                if departure is not None:
                    departure_dt = utils.safe_strptime(departure)
                else:
                    departure_dt = arrival_dt + timedelta(seconds=0.0)

            else:
                departure_dt = utils.safe_strptime(stage.get("end_time", "24:00:00"))

            if departure_dt < arrival_dt:
                logger.debug(f"Negative duration activity found at pid={person_id}")

            plan.add(
                activity.Activity(
                    seq=act_seq,
                    act=act_type,
                    loc=loc,
                    link=stage.get("link"),
                    start_time=arrival_dt,
                    end_time=departure_dt,
                )
            )

        if stage.tag == "leg":
            mode, route, attributes = unpack_leg(stage, version)
            if not leg_attributes:
                attributes = {}

            leg_seq += 1
            trav_time = stage.get("trav_time")
            if trav_time is not None:
                leg_duration = utils.safe_strpdelta(trav_time)
                arrival_dt = departure_dt + leg_duration
            else:
                arrival_dt = departure_dt  # todo this assumes 0 duration unless known

            if not leg_route:
                # Optionally ignores route info such as links, distance and so on.
                plan.add(
                    activity.Leg(
                        seq=leg_seq,
                        mode=mode,
                        start_time=departure_dt,
                        end_time=arrival_dt,
                        attributes=attributes,
                    )
                )

            else:
                plan.add(
                    activity.Leg(
                        seq=leg_seq,
                        mode=mode,
                        start_link=route.get("start_link"),
                        end_link=route.get("end_link"),
                        start_time=departure_dt,
                        end_time=arrival_dt,
                        distance=route.distance,
                        attributes=attributes,
                        route=route,
                    )
                )

    if simplify_pt_trips:
        plan.simplify_pt_trips()

    plan.set_leg_purposes()

    score = plan_xml.get("score", None)
    if score:
        score = float(score)
    plan.score = score  # experienced plan scores

    if crop:
        plan.crop()
    if autocomplete:
        plan.autocomplete_matsim()

    return plan


def unpack_leg(leg, version):
    if version == 12:
        return unpack_leg_v12(leg)
    return unpack_route_v11(leg)


def unpack_route_v11(leg) -> tuple[str, RouteV11, dict]:
    """Extract mode, network route and transit route as available.

    Args:
        leg (xml_leg_element):

    Returns:
        tuple[str, RouteV11, dict]: mode, route, attributes
    """
    mode = leg.get("mode")
    route = RouteV11(leg.xpath("route"))
    return mode, route, {}


def unpack_leg_v12(leg) -> tuple[str, Route, dict]:
    """Extract mode, route and attributes as available.

    Args:
        leg (xml_leg_element):

    Returns:
        tuple[str, Route, dict]: mode, route, attributes

    Example:
        There are four known cases:

        === Unrouted ===

        For example a leg missing both attributes and route elements, this is the case for non experienced or non routed plans:
        ```xml
            <leg mode="car" dep_time="07:00:00" trav_time="00:07:34">
            </leg>
        ```

        === Transit ===

        This is a transit routed leg with the route encoded as json string and routingMode attribute:
        ```xml
            <leg mode="pt" trav_time="00:43:42">
                <attributes>
                    <attribute name="routingMode" class="java.lang.String">bus</attribute>
                </attributes>
                <route type="default_pt" start_link="1-2" end_link="3-4" trav_time="00:43:42" distance="10100.0">
                {"transitRouteId":"work_bound","boardingTime":"07:30:00","transitLineId":"city_line","accessFacilityId":"home_stop_out","egressFacilityId":"work_stop_in"}
                </route>
            </leg>
        ```

        Route must be transit i.e. there will not be a network route.
        Route attributes include:
            - type = "default_pt"
            - start_link
            - end_link
            - trav_time
            - distance

        === Network Routed ===

        This is a network routed mode, eg car:
        ``` xml
            <leg mode="car" dep_time="07:58:00" trav_time="00:04:52">
                <attributes>
                    <attribute name="enterVehicleTime" class="java.lang.Double">28680.0</attribute>
                    <attribute name="routingMode" class="java.lang.String">car</attribute>
                </attributes>
                <route type="links" start_link="4155" end_link="5221366698030330427_5221366698041252619" trav_time="00:04:52" distance="4898.473995989452" vehicleRefId="null">
                4155 5221366345330551489_5221366345327939575 2623 4337 5221366343808222067_5221366343837130911 2984 1636 3671 6110 etc...
                </route>
            </leg>
        ```

        Route attributes include:
            - type = "links"
            - start_link
            - end_link
            - trav_time
            - distance
            - vehicleRefId
        The network route is given as a space seperated sequence of link ids.

        === Teleported ===

        This is a teleported route, eg walk/cycle:
        ``` xml
            <leg mode="walk" dep_time="09:23:00" trav_time="01:54:10">
                <attributes>
                    <attribute name="routingMode" class="java.lang.String">walk</attribute>
                </attributes>
                <route type="generic" start_link="5221366698030330427_5221366698041252619" end_link="114" trav_time="01:54:10" distance="5710.003987453454"></route>
            </leg>
        ```

        Route attributes include:
            - type = "generic"
            - start_link
            - end_link
            - trav_time
            - distance
        The network route is empty.
    """
    mode = leg.get("mode")
    route = Route(leg.xpath("route"))
    attributes = get_attributes_from_legs(leg)
    return mode, route, attributes


def load_attributes_map_from_v12(plans_path):
    return dict(
        [get_attributes_from_person(elem) for elem in utils.get_elems(plans_path, "person")]
    )


def get_attributes_from_person(elem):
    ident = elem.xpath("@id")[0]
    attributes = {}
    for attr in elem.xpath("./attributes/attribute"):
        attribute_type = attr.get("class")
        attribute_name = attr.get("name")
        if attribute_type == "java.lang.String":
            attributes[attribute_name] = attr.text
        elif attribute_type == "java.lang.Boolean":
            attributes[attribute_name] = attr.text.lower() == "true"
        elif attribute_type == "java.lang.Integer":
            attributes[attribute_name] = int(attr.text)
        elif attribute_type == "java.lang.Double":
            attributes[attribute_name] = float(attr.text)
        elif attribute_type == "org.matsim.vehicles.PersonVehicles":
            attributes[attribute_name] = parse_veh_attribute(attr.text)
        # last try:
        else:
            attributes[attribute_name] = attr.text
    return ident, attributes


def parse_veh_attribute(text) -> dict:
    return json.loads(text)


def get_attributes_from_legs(elem):
    attributes = {}
    for attr in elem.xpath("./attributes/attribute"):
        attributes[attr.get("name")] = attr.text
    return attributes


def load_attributes_map(attributes_path):
    """Given path to MATSim attributes input, return dictionary of attributes (as dict)."""
    attributes_map = {}
    people = utils.get_elems(attributes_path, "object")
    for person in people:
        att_map = {}
        for attribute in person:
            att_map[attribute.get("name")] = attribute.text
        attributes_map[person.get("id")] = att_map

    return attributes_map


def selected_plans(plans_path):
    """Given path to MATSim plans input, yield person id and plan for all selected plans."""
    for person in utils.get_elems(plans_path, "person"):
        for plan in person:
            if plan.get("selected") == "yes":
                yield person.get("id"), plan
