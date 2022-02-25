import pytest
from pam.core import Person
from pam.vehicle import Vehicle, ElectricVehicle
from pam import PAMVehicleIdError


def test_instantiating_vehicle_without_id_fails():
    with pytest.raises(TypeError) as error_info:
        default_vehicle = Vehicle()
    assert "required positional argument: 'id'" in str(error_info.value)


def test_instantiating_electric_vehicle_without_id_fails():
    with pytest.raises(TypeError) as error_info:
        e_vehicle = ElectricVehicle()
    assert "required positional argument: 'id'" in str(error_info.value)


def test_instantiating_person_with_vehicle_without_matching_id_fails():
    with pytest.raises(PAMVehicleIdError) as error_info:
        p = Person(pid='1', vehicle=Vehicle(id='2'))
    assert "does not match Person ID" in str(error_info.value)


def test_assigning_with_nonmatching_id_vehicle_to_person_fails():
    p = Person(pid='1')
    with pytest.raises(PAMVehicleIdError) as error_info:
        p.assign_vehicle(vehicle=Vehicle(id='2'))
    assert "does not match Person ID" in str(error_info.value)
