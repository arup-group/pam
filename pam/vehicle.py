from dataclasses import dataclass
from typing import Union
from lxml import etree as et


# Vehicle definition Classes based on MATSim DTD file:
# https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd


@dataclass(frozen=True)
class CapacityType:
    seats: int = 4  # persons
    standingRoomInPersons: int = 0  # persons

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
    id: str
    vehicle_type: VehicleType = VehicleType()

    def __lt__(self, other):
        return self.id < other.id

    def to_xml(self, xf):
        xf.write(et.Element("vehicle", {'id': str(self.id), 'type': str(self.vehicle_type.id)}))


@dataclass(frozen=True)
class ElectricVehicle(Vehicle):
    vehicle_type: VehicleType = VehicleType(id='defaultElectricVehicleType')
    battery_capacity: float = 60  # kWh
    initial_soc: float = battery_capacity  # kWh
    charger_types: str = 'default'  # supported charger types; comma-separated list: 'default,other'

    def to_e_xml(self, xf):
        xf.write(
            et.Element("vehicle",
                       {'id': str(self.id), 'battery_capacity': str(self.battery_capacity),
                        'initial_soc': str(self.initial_soc), 'charger_types': str(self.charger_types),
                        'vehicle_type': str(self.vehicle_type.id)}
        ))
