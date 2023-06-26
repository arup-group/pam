from dataclasses import dataclass
from lxml import etree as et
from typing import Optional, Union
import logging
from enum import Enum


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
        xf.write(et.Element("capacity",
                            {'seats': str(self.seats), 'standingRoomInPersons': str(self.standingRoomInPersons)}))


@dataclass(frozen=True)
class VehicleType:
    id: str = 'defaultVehicleType'
    length: float = 7.5  # metres
    width: float = 1.0  # metres
    networkMode: str = 'car'
    capacity: CapacityType = CapacityType()
    description: str = 'personal_vehicle'
    passengerCarEquivalents: float = 1.0
    flowEfficiencyFactor: float = 1.0

    @classmethod
    def from_xml_elem(cls, elem):
        attribs = {attrib.tag.replace('{http://www.matsim.org/files/dtd}', ''): attrib for attrib in elem}
        return cls(
            id=elem.get('id'),
            length=float(attribs["length"].attrib['meter']),
            width=float(attribs["width"].attrib['meter']),
            passengerCarEquivalents=float(attribs["passengerCarEquivalents"].attrib['pce']),
            networkMode=attribs["networkMode"].attrib['networkMode'],
            flowEfficiencyFactor=float(attribs["flowEfficiencyFactor"].attrib['factor']),
            capacity=CapacityType.from_xml_elem(attribs['capacity']),
            description=attribs['description'].text
        )

    def to_xml(self, xf):
        with xf.element("vehicleType", {'id': self.id}):
            rec = et.Element("description")
            rec.text = self.description
            xf.write(rec)
            self.capacity.to_xml(xf)
            xf.write(et.Element("length", {'meter': str(self.length)}))
            xf.write(et.Element("width", {'meter': str(self.width)}))
            xf.write(et.Element("passengerCarEquivalents", {'pce': str(self.passengerCarEquivalents)}))
            xf.write(et.Element("networkMode", {'networkMode': str(self.networkMode)}))
            xf.write(et.Element("flowEfficiencyFactor", {'factor': str(self.flowEfficiencyFactor)}))


@dataclass(frozen=True)
class Vehicle:
    type_id: str

    def to_xml(self, xf, vid):
        xf.write(et.Element("vehicle", {'id': str(vid), 'type': str(self.type_id)}))


@dataclass(frozen=True)
class ElectricVehicle(Vehicle):
    battery_capacity: float = 60  # kWh
    initial_soc: float = battery_capacity  # kWh
    charger_types: str = 'default'  # supported charger types; comma-separated list: 'default,other'

    def to_xml(self, xf, vid):
        xf.write(
            et.Element("vehicle",
                       {'id': str(vid), 'battery_capacity': str(self.battery_capacity),
                        'initial_soc': str(self.initial_soc), 'charger_types': str(self.charger_types),
                        'vehicle_type': str(self.type_id)}
                       )
        )


class VehicleTypes:
    veh_types: dict
    mapping: dict

    def get(self, key, default:Optional[VehicleType]=None):
        return self.veh_types.get(self.mapping[key], default)
    
    def add_type(self, vehicle_type: VehicleType) -> bool:

        if vehicle_type.id not in self.veh_types:
            self.veh_types[vehicle_type.id] = vehicle_type
            return True
        return False
    
    def __additem__(self, key: str, value: Union[Vehicle, ElectricVehicle, VehicleType]):
        if isinstance(value, Vehicle) or isinstance(value, ElectricVehicle):
            if not value.type_id in self.veh_types:
                logging.info(f"Failed to add vehicle, the vehicle type '{value.type_id}' is an unknown veh type.")
            self.mapping[key] = value
        elif isinstance(value, VehicleType):
            self.add_type(value)
            self.mapping[key] = Vehicle(value.id)
        else:
            raise UserWarning(f"Unsupported type {type(value)}, please use 'Union[Vehicle, ElectricVehicle, VehicleType]'.")
    
    def __getitem__(self, veh_id) -> str:
        return self.mapping[veh_id]

    def __iter__(self):
        for veh_id, type_id in self.mapping.items():
            yield veh_id, self.veh_types[type_id]
    
    def is_consistent(self):
        for k, v in self.mapping.items():
            if v not in self.veh_types:
                logging.info(f"Failed to find veh type of id '{v}', specified for veh id '{k}'.")
                return False
        return True
            
    def to_xml(
        self,
        path,
        ):
        """
        Writes all_vehicles file following format https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd
        for MATSim
        :param path: name of output file, defaults to 'all_vehicles.xml`
        :return: None
        """
        logging.info(f'Writing vehicle types to {path}')

        with et.xmlfile(path, encoding="utf-8") as xf:
            xf.write_declaration()
            vehicleDefinitions_attribs = {
                'xmlns': "http://www.matsim.org/files/dtd",
                'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                'xsi:schemaLocation': "http://www.matsim.org/files/dtd "
                                    "http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd"}
            with xf.element("vehicleDefinitions", vehicleDefinitions_attribs):
                for vehicle_type in self.veh_types.values():
                    vehicle_type.to_xml(xf)
                for vid, veh in self.mapping.sort().items():
                    veh.to_xml(xf, vid)