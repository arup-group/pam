from dataclasses import dataclass
from typing import Union


# Vehicle definition Classes based on MATSim DTD file:
# https://www.matsim.org/files/dtd/vehicleDefinitions_v1.0.xsd


@dataclass(frozen=True)
class CapacityType:
    seats: int = 4  # persons
    standingRoom: int = 0  # persons


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
    maximumVelocity: Union[float, str] = 'INF'  # meterPerSecond
    accessTime: float = 1.0  # secondsPerPerson
    egressTime: float = 1.0  # secondsPerPerson
    doorOperation: str = 'serial'


@dataclass(frozen=True)
class Vehicle:
    id: str
    vehicle_type: VehicleType = VehicleType()


@dataclass(frozen=True)
class ElectricVehicle(Vehicle):
    vehicle_type: VehicleType = VehicleType(id='defaultElectricVehicleType')
    battery_capacity: float = 60  # kWh
    initial_soc: float = battery_capacity  # kWh
    charger_types: str = 'default'  # supported charger types; comma-separated list: 'default,other'
