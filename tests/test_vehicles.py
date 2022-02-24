import pytest
from pam.vehicle import Vehicle, ElectricVehicle


def test_instantiating_vehicle_without_id_fails():
    with pytest.raises(TypeError) as error_info:
        default_vehicle = Vehicle()
    assert "required positional argument: 'id'" in str(error_info.value)


def test_instantiating_electric_vehicle_without_id_fails():
    with pytest.raises(TypeError) as error_info:
        e_vehicle = ElectricVehicle()
    assert "required positional argument: 'id'" in str(error_info.value)
