from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from lxml import etree as et

import pam.utils as utils
from pam import PAMVehicleIdError, PAMVehicleTypeError

# Vehicle classes to represent Vehicles based on MATSim DTD files:
# https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
# https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd


@dataclass
class CapacityType:
    """Vehicle capacity dataclass with read/write methods.

    Attributes:
        seats (int): Seats in/on vehicle.
        standingRoomInPersons (int): Standing room in/on vehicle.
    """

    seats: int = 4  # persons
    standingRoomInPersons: int = 0  # persons

    @classmethod
    def from_xml_elem(cls, elem):
        attribs = {k: int(v) for k, v in elem.attrib.items()}
        return cls(**attribs)

    def to_xml(self, xf):
        xf.write(
            et.Element(
                "capacity",
                {
                    "seats": str(self.seats),
                    "standingRoomInPersons": str(self.standingRoomInPersons),
                },
            )
        )


@dataclass
class VehicleType:
    """Vehicle type data with read/write methods.

    Attributes:
        id (str): type id.
        length (float): Vehicle length in m.
        width (float): Vehicle width in m.
        networkMode (str): MATSim network mode (used for routing).
        capacity (CapacityType): Vehicle seating and standing capacity.
        description (str): Vehicle description.
        passengerCarEquivalents (float): Vehicle size as passenger car equivalents (PCUs).
        flowEfficiencyFactor (float): Vehicle flow efficiency factor.
    """

    id: str
    length: float = 7.5  # metres
    width: float = 1.0  # metres
    networkMode: str = "car"
    capacity: CapacityType = field(default_factory=CapacityType)
    description: str = "personal_vehicle"
    passengerCarEquivalents: float = 1.0
    flowEfficiencyFactor: float = 1.0

    @classmethod
    def from_xml_elem(cls, elem: et.Element) -> VehicleType:
        """Construct VehicleType from MATSim xml element.

        Args:
            elem (et.Element): MATSim formatted vehicle type xml element.

        Returns:
            VehicleType: Vehicle type dataclass.
        """
        attribs = {
            attrib.tag.replace("{http://www.matsim.org/files/dtd}", ""): attrib for attrib in elem
        }
        return cls(
            id=elem.get("id"),
            length=float(attribs["length"].attrib["meter"]),
            width=float(attribs["width"].attrib["meter"]),
            passengerCarEquivalents=float(attribs["passengerCarEquivalents"].attrib["pce"]),
            networkMode=attribs["networkMode"].attrib["networkMode"],
            flowEfficiencyFactor=float(attribs["flowEfficiencyFactor"].attrib["factor"]),
            capacity=CapacityType.from_xml_elem(attribs["capacity"]),
            description=attribs["description"].text,
        )

    def to_xml(self, xf: et.Element) -> None:
        """Write vehicle type to MATSim formatted xml.

        Args:
            xf (et.Element): Parent xml element.
        """
        with xf.element("vehicleType", {"id": self.id}):
            rec = et.Element("description")
            rec.text = self.description
            xf.write(rec)
            self.capacity.to_xml(xf)
            xf.write(et.Element("length", {"meter": str(self.length)}))
            xf.write(et.Element("width", {"meter": str(self.width)}))
            xf.write(
                et.Element("passengerCarEquivalents", {"pce": str(self.passengerCarEquivalents)})
            )
            xf.write(et.Element("networkMode", {"networkMode": str(self.networkMode)}))
            xf.write(et.Element("flowEfficiencyFactor", {"factor": str(self.flowEfficiencyFactor)}))


@dataclass
class Vehicle:
    """Vehicle parent data class, holds required vehicle data (id and type) and read/write methods.

    Attributes:
        vid (str): Unique vehicle identifier.
        type_id (str): Type of vehicle, eg "default_car".
    """

    vid: str
    type_id: str

    def to_xml(self, xf: et.Element) -> None:
        """Write vehicle to MATSim formatted xml.

        Args:
            xf (et.Element): Parent xml element.
        """
        xf.write(et.Element("vehicle", {"id": str(self.vid), "type": str(self.type_id)}))


@dataclass
class ElectricVehicle(Vehicle):
    """Electric vehicle data representation. Required for MATSim EV extension.

    Attributes:
        vid (str): Unique vehicle identifier.
        type_id (str): Type of vehicle, eg "default_car".
        battery_capacity (float): Charge capacity.
        initial_soc (float): Initial state of charge.
        charger_types (str): Types of chargers vehicle may use.
    """

    battery_capacity: float = 60  # kWh
    initial_soc: float = battery_capacity  # kWh
    charger_types: str = "default"  # supported charger types; comma-separated list: 'default,other'

    def to_ev_xml(self, xf) -> None:
        """Write vehicle to MATSim formatted xml.

        Args:
            xf (et.Element): Parent xml element.
        """
        xf.write(
            et.Element(
                "vehicle",
                {
                    "id": str(self.vid),
                    "battery_capacity": str(self.battery_capacity),
                    "initial_soc": str(self.initial_soc),
                    "charger_types": str(self.charger_types),
                    "vehicle_type": str(self.type_id),
                },
            )
        )


class VehicleManager:
    """
    Vehicles and vehicle types representation, responsible for read/write from MATSim vehicles files.

    Attributes:
        _veh_types (dict[str, VehicleType]): Mapping of type ids to vehicle types data.
        _vehicles (dict[str, Vehicle]): Mapping of vehicle ids to vehicle data.
    """

    _veh_types: dict[str, VehicleType]
    _vehicles: dict[str, Vehicle]

    def __init__(self) -> None:
        self._veh_types = {}
        self._vehicles = {}

    def add_type(self, vehicle_type: VehicleType) -> None:
        """Add vehicle type to manager.

        Args:
            vehicle_type (VehicleType): Vehicle type dataclass.
        """
        if vehicle_type.id in self._veh_types:
            logging.info(f"Warning, overwriting existing vehicle type '{vehicle_type.id}'.")
        self._veh_types[vehicle_type.id] = vehicle_type

    def remove_type(self, tid: str):
        """Remove vehicle type.

        Args:
            tid (str): Vehicle type id.
        """
        logging.info("Warning, removing a vehicle type may invalidate your vehicles.")
        if self._veh_types.pop(tid, None) is None:
            raise PAMVehicleTypeError(f"Failed to remove vehicle type {tid}, id not found.")

    def add_veh(self, v: Vehicle):
        """Add vehicle to manager.

        Args:
            v (Vehicle): Vehicle dataclass.

        Raises:
            PAMVehicleIdError: Unknown vehicle type.
        """
        if v.type_id not in self._veh_types:
            raise PAMVehicleTypeError(
                f"Failed to add vehicle: {v.vid}, the vehicle type '{v.type_id}' is an unknown veh type."
            )
        if v.vid in self._vehicles:
            logging.info(f"Warning, overwriting existing vehicle: '{v.vid}'.")
        self._vehicles[v.vid] = v

    def __setitem__(self, k: str, v: Vehicle):
        if isinstance(v, ElectricVehicle):
            self.add_veh(v)
        elif isinstance(v, Vehicle):
            self.add_veh(v)
        else:
            raise UserWarning(
                f"Unsupported type {type(v)}, please use 'Union[Vehicle, ElectricVehicle]'."
            )

    def __getitem__(self, k) -> Vehicle:
        return self._vehicles[k]

    def get(self, k: str, default: Optional[Vehicle] = None) -> Optional[Vehicle]:
        return self._vehicles.get(k, default)

    def len(self) -> int:
        """Number of vehicles."""
        return len(self._vehicles)

    def __contains__(self, k: str):
        return k in self._vehicles

    def __eq__(self, other):
        if not self._veh_types == other._veh_types:
            return False
        if not self._vehicles == other._vehicles:
            return False
        return True

    def pop(self, vid):
        return self._vehicles.pop(vid)

    @property
    def evs(self) -> dict[str, ElectricVehicle]:
        """Return dictionary of electric vehicles in manager.

        Returns:
            dict[str, ElectricVehicle]: Dictionary of electric vehicles.
        """
        return {vid: veh for vid, veh in self._vehicles.items() if isinstance(veh, ElectricVehicle)}

    def charger_types(self) -> set[str]:
        """Return set of electric charger types used by evs.

        Returns:
            set[str]: Electric charger types.
        """
        chargers = set()
        for v in self.evs.values():
            chargers |= set(v.charger_types.split(","))
        return chargers

    def is_consistent(self) -> bool:
        """Check that manager vehicle population and types are consistent.

        Raises:
            PAMVehicleIdError: Unknown vehicle type.

        Returns:
            bool: Manager is consistent. Note that this doesn't check for unused types.
        """
        veh_types = set(self._veh_types.keys())
        for k, v in self._vehicles.items():
            if v.type_id not in veh_types:
                raise PAMVehicleIdError(
                    f"Failed to find veh type of id '{v}', specified for veh id '{k}'."
                )
        return True

    def redundant_types(self) -> dict:
        """Check for ununsed vehicle types.

        Returns:
            dict: unused types.
        """
        unused = {}
        veh_types = set(self._veh_types.keys())
        veh_veh_types = set([v.type_id for v in self._vehicles.values()])
        for t in veh_types:
            if t not in veh_veh_types:
                unused[t] = self._veh_types[t]
        return unused

    def clear_types(self):
        """Remove all types from manager."""
        self._veh_types = {}

    def clear_vehs(self):
        """Remove all vehciles from manager."""
        self._vehicles = {}

    def from_xml(self, vehs_path: str, evs_path: Optional[str] = None):
        """Reads MATSim vehicles from https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        and reads electric_vehicles from https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd.
        Requires a vehicles file to load an evs file because the electric vehicle type is expected to be defined in
        the vehicles input.

        Args:
            vehs_path (str): path to matsim all_vehicles xml file
            evs_path (Optional[str], optional): optional path to matsim electric_vehicles xml file. Defaults to None.

        Raises:
            UserWarning: Cannot load evs without a vehs file.
            UserWarning: Fails consistency check.
        """

        if not vehs_path and evs_path:
            raise UserWarning("Cannot load an evs file without a vehs file.")
        self.types_from_xml(vehs_path)
        self.vehs_from_xml(vehs_path)
        if evs_path is not None:
            self.evs_from_xml(evs_path)
        if not self.is_consistent():
            raise UserWarning("Inputs not consistent, refer to log.")

    def types_from_xml(self, path: str):
        """Reads vehicle types from MATSim vehicles file (https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd).

        Args:
            path (str): path to matsim all_vehicles xml file
        """
        vehs = dict(
            (elem.get("id"), VehicleType.from_xml_elem(elem))
            for elem in utils.get_elems(path, "vehicleType")
        )
        keys = set(vehs) & set(self._veh_types)
        if keys:
            raise PAMVehicleIdError(
                f"Failed to read types from xml due to duplicate keys with existing types: {keys}"
            )
        self._veh_types.update(vehs)

    def vehs_from_xml(self, path: str):
        """Reads vehicles from MATSim vehicles file (https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd).

        Args:
            path (str): path to matsim all_vehicles xml file
        """

        vehs = {
            elem.get("id"): Vehicle(vid=elem.get("id"), type_id=elem.get("type"))
            for elem in utils.get_elems(path, "vehicle")
        }
        keys = set(vehs) & set(self._vehicles)
        if keys:
            raise PAMVehicleIdError(
                f"Failed to read vehs from xml due to duplicate keys with existing: {keys}"
            )
        self._vehicles.update(vehs)

    def evs_from_xml(self, path):
        """Reads vehicles from MATSim vehicles file (https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd).

        Args:
            path (str): path to matsim all_vehicles xml file
        """
        evs = {}
        for vehicle_elem in utils.get_elems(path, "vehicle"):
            attribs = dict(vehicle_elem.attrib)
            vid = attribs.pop("id")
            vehicle_type = attribs.pop("vehicle_type")
            attribs["battery_capacity"] = float(attribs["battery_capacity"])
            attribs["initial_soc"] = float(attribs["initial_soc"])
            evs[vid] = ElectricVehicle(vid=vid, type_id=vehicle_type, **attribs)
        keys = set(evs) & set(self._vehicles)
        if keys:
            PAMVehicleIdError(
                f"Failed to read evs from xml due to duplicate keys with existing: {keys}"
            )
        self._vehicles.update(evs)

    def to_xml(self, vehs_path: str, evs_path: Optional[str] = None):
        """Write manager to MATSim formatted xml.

        Args:
            vehs_path (str): Write path for MATSim vehicles file.
            evs_path (Optional[str], optional): Write path for MATSim electric vehicles file. Defaults to None.
        """
        self.to_veh_xml(vehs_path)
        if evs_path:
            self.to_ev_xml(evs_path)

    def to_veh_xml(self, path: str):
        """Writes MATSim vehicles file as per https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd.

        Args:
            path (str): name of output file.
        """
        with et.xmlfile(path, encoding="utf-8") as xf:
            xf.write_declaration()
            vehicleDefinitions_attribs = {
                "xmlns": "http://www.matsim.org/files/dtd",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.matsim.org/files/dtd "
                "http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd",
            }
            with xf.element("vehicleDefinitions", vehicleDefinitions_attribs):
                logging.info(f"Writing vehicle types to {path}")
                for vehicle_type in self._veh_types.values():
                    vehicle_type.to_xml(xf)
                logging.info(f"Writing vehicles to {path}")
                for veh in self._vehicles.values():
                    veh.to_xml(xf)

    def to_ev_xml(self, path: str):
        """Writes MATSim electric vehciles file as per https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd.

        Args:
            path (str): name of output file
        """
        with et.xmlfile(path, encoding="utf-8") as xf:
            logging.info(f"Writing electric vehicles to {path}")
            xf.write_declaration(
                doctype='<!DOCTYPE vehicles SYSTEM "http://matsim.org/files/dtd/electric_vehicles_v1.dtd">'
            )
            with xf.element("vehicles"):
                for veh in self.evs.values():
                    veh.to_ev_xml(xf)
