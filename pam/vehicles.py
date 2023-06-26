from dataclasses import dataclass
from lxml import etree as et
from typing import Optional, Union, TypeVar, Type
import logging
from enum import Enum
from pam.core import Population
import pam.utils as utils


# Vehicle classes to represent Vehicles based on MATSim DTD files:
# https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
# https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd


@dataclass(frozen=True)
class CapacityType:
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


@dataclass(frozen=True)
class VehicleType:
    id: str = "defaultVehicleType"
    length: float = 7.5  # metres
    width: float = 1.0  # metres
    networkMode: str = "car"
    capacity: CapacityType = CapacityType()
    description: str = "personal_vehicle"
    passengerCarEquivalents: float = 1.0
    flowEfficiencyFactor: float = 1.0

    @classmethod
    def from_xml_elem(cls, elem):
        attribs = {
            attrib.tag.replace("{http://www.matsim.org/files/dtd}", ""): attrib
            for attrib in elem
        }
        return cls(
            id=elem.get("id"),
            length=float(attribs["length"].attrib["meter"]),
            width=float(attribs["width"].attrib["meter"]),
            passengerCarEquivalents=float(
                attribs["passengerCarEquivalents"].attrib["pce"]
            ),
            networkMode=attribs["networkMode"].attrib["networkMode"],
            flowEfficiencyFactor=float(
                attribs["flowEfficiencyFactor"].attrib["factor"]
            ),
            capacity=CapacityType.from_xml_elem(attribs["capacity"]),
            description=attribs["description"].text,
        )

    def to_xml(self, xf):
        with xf.element("vehicleType", {"id": self.id}):
            rec = et.Element("description")
            rec.text = self.description
            xf.write(rec)
            self.capacity.to_xml(xf)
            xf.write(et.Element("length", {"meter": str(self.length)}))
            xf.write(et.Element("width", {"meter": str(self.width)}))
            xf.write(
                et.Element(
                    "passengerCarEquivalents",
                    {"pce": str(self.passengerCarEquivalents)},
                )
            )
            xf.write(et.Element("networkMode", {"networkMode": str(self.networkMode)}))
            xf.write(
                et.Element(
                    "flowEfficiencyFactor", {"factor": str(self.flowEfficiencyFactor)}
                )
            )


@dataclass(frozen=True)
class Vehicle:
    vid: str
    type_id: str

    def to_xml(self, xf):
        xf.write(
            et.Element("vehicle", {"id": str(self.vid), "type": str(self.type_id)})
        )


@dataclass(frozen=True)
class ElectricVehicle(Vehicle):
    battery_capacity: float = 60  # kWh
    initial_soc: float = battery_capacity  # kWh
    charger_types: str = (
        "default"  # supported charger types; comma-separated list: 'default,other'
    )

    def to_xml(self, xf):
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
    Container and general methods for a 'vehicle population'.
    'veh_types' is a dictionary of vehicle types.
    'vehs' and 'evs' are both dictionaries mapping veh ids ('vids') to vehicles.
    Vehicles may be either regular Vehicles which simple hold a reference to vehicle type.
    Or ElectricVehicles which additionally contain EV specific attributes such as charge state.
    """

    veh_types: dict
    vehs: dict
    evs: dict

    def __init__(self) -> None:
        self.veh_types = {}
        self.vehs = {}
        self.evs = {}

    def get(self, key, default: Optional[VehicleType] = None):
        return self.veh_types.get(self.vehs[key], default)

    def get_ev(self, key, default: Optional[VehicleType] = None):
        return self.veh_types.get(self.evs[key], default)

    def add_type(self, vehicle_type: VehicleType):
        if vehicle_type.id in self.veh_types:
            logging.info(
                f"Warning, overwriting existing vehicle type '{vehicle_type.id}'."
            )
        self.veh_types[vehicle_type.id] = vehicle_type

    def add_veh(self, k: str, v: Vehicle) -> bool:
        if not v in self.veh_types:
            logging.info(
                f"Failed to add vehicle, the vehicle type '{v.type_id}' is an unknown veh type."
            )
            return False
        if k in self.vehs:
            logging.info(f"Warning, overwriting existing vehicle: '{k}'.")
        self.vehs[k] = v

    def add_ev(self, k: str, v: ElectricVehicle) -> bool:
        if not v in self.veh_types:
            logging.info(
                f"Failed to add vehicle, the vehicle type '{v.type_id}' is an unknown veh type."
            )
            return False
        if k in self.evs:
            logging.info(f"Warning, overwriting existing ev: '{k}'.")
        self.evs[k] = v

    def __additem__(self, k: str, v: Union[Vehicle, ElectricVehicle]):
        if isinstance(v, Vehicle):
            self.add_veh(k, v)
        elif isinstance(v, ElectricVehicle):
            self.add_ev(k, v)
        else:
            raise UserWarning(
                f"Unsupported type {type(v)}, please use 'Union[Vehicle, ElectricVehicle]'."
            )

    def __getitem__(self, k) -> Vehicle:
        if k in self.vehs:
            if k in self.evs:
                raise UserWarning(f"Duplicate veh id: '{k}' found in vehs and evs")
            return self.vehs[k]
        return self.evs[k]

    def __iter__(self):
        for veh_id, type_id in self.vehs.items():
            yield veh_id, self.veh_types[type_id]
        for veh_id, type_id in self.evs.items():
            yield veh_id, self.veh_types[type_id]

    def len(self):
        return len(self.vehs) + len(self.evs)

    def types(self):
        for tid, t in self.veh_types.items():
            yield tid, t

    def vehs(self):
        for vid, veh in self.vehs.items():
            yield vid, veh

    def evs(self):
        for vid, veh in self.evs.items():
            yield vid, veh

    def electric_vehicle_charger_types(self):
        chargers = set()
        for _, _, _, v in self.evs():
            chargers |= set(v.charger_types.split(","))
        return chargers

    def is_consistent(self):
        veh_types = set(self.veh_types.keys())
        ev_keys = set(self.evs.keys())
        for k, v in self.vehs.items():
            if v not in veh_types:
                logging.info(
                    f"Failed to find veh type of id '{v}', specified for veh id '{k}'."
                )
                return False
            if k in ev_keys:
                logging.info(f"Duplicate id '{k}', found in vehs and evs.")
                return False
        for k, v in self.evs.items():
            if v not in veh_types:
                logging.info(
                    f"Failed to find ev type of id '{v}', specified for ev id '{k}'."
                )
                return False
        for t in veh_types:
            if t not in self.vehs and t not in self.evs:
                logging.info(f"Unused veh type: '{t}'.")
                return False
        return True

    def clear(self):
        self.vehs = {}
        self.evs = {}

    def from_population(self, population: Population):
        """
        (Re)build veh population from agents.
        """
        self.clear()
        for _, _, mode, veh in population.vehicles():
            self[veh.vid] = veh
        if not self.is_consistent():
            raise UserWarning("Failed consistency check refer to logs.")

    def from_xml(self, vehs_path: str, evs_path: Optional[str]):
        """
        Reads all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        and reads electric_vehicles file following format https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd
        :param vehs_path: path to matsim all_vehicles xml file
        :param evs_path: path to matsim electric_vehicles xml file
        """
        if not vehs_path and evs_path:
            raise UserWarning("Cannot load an evs file without a vehs file.")
        self.types_from_xml(vehs_path)
        self.vehs_from_xml(vehs_path)
        self.evs_from_xml(evs_path)
        if not self.is_consistent():
            raise UserWarning("Inputs not consistent, refer to log.")

    def types_from_xml(self, path):
        """
        Reads all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        :param path: path to matsim all_vehicles xml file
        :return: dictionary of all vehicles: {ID: pam.vehicle.Vehicle class object}
        """
        self.veh_types = {
            elem.get("id"): VehicleType.from_xml_elem(elem)
            for elem in utils.get_elems(path, "vehicleType")
        }

    def vehs_from_xml(self, path):
        """
        Reads all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        :param path: path to matsim all_vehicles xml file
        :return: dictionary of all vehicles: {ID: pam.vehicle.Vehicle class object}
        """
        self.vehs = {
            elem.get("id"): Vehicle(id=elem.get("id"), vehicle_type=elem.get("type"))
            for elem in utils.get_elems(path, "vehicle")
        }

    def evs_from_xml(self, path):
        evs = {}
        for vehicle_elem in utils.get_elems(path, "vehicle"):
            attribs = dict(vehicle_elem.attrib)
            vid = attribs.pop("vid")
            vehicle_type = attribs.pop("vehicle_type")
            attribs["battery_capacity"] = float(attribs["battery_capacity"])
            attribs["initial_soc"] = float(attribs["initial_soc"])
            evs[id] = ElectricVehicle(id=vid, vehicle_type=vehicle_type, **attribs)
        self.evs = evs

    def to_xml(
        self,
        vehs_path: str,
        evs_path: Optional[str],
    ):
        self.to_veh_xml(vehs_path)
        if evs_path:
            self.to_ev_xml(evs_path)

    def to_veh_xml(
        self,
        path,
    ):
        """
        Writes all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        for MATSim
        :param path: name of output file, defaults to 'all_vehicles.xml`
        :return: None
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
                for vehicle_type in self.veh_types.values():
                    vehicle_type.to_xml(xf)
                logging.info(f"Writing vehicles to {path}")
                for _, veh in self.vehs.sort().items():
                    veh.to_xml(xf)

    def to_ev_xml(self, path):
        """
        Writes electric vehciles file to following format https://www.matsim.org/files/dtd/electric_vehicles_v1.dtd
        for MATSim
        :param path: name of output file
        :return: None
        """
        with et.xmlfile(path, encoding="utf-8") as xf:
            logging.info(f"Writing electric vehicles to {path}")
            xf.write_declaration(
                doctype='<!DOCTYPE vehicles SYSTEM "http://matsim.org/files/dtd/electric_vehicles_v1.dtd">'
            )
            with xf.element("vehicles"):
                for _, veh in self.evs.sort().items():
                    veh.to_xml(xf)
