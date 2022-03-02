import pytest
from pam.core import Person, Population, Household
from pam.vehicle import Vehicle, ElectricVehicle, VehicleType
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


@pytest.fixture()
def person_without_a_vehicle():
    return Person('Bobby', attributes={'age': 6, 'job': 'education', 'gender': 'non-binary'})


@pytest.fixture()
def person_with_default_vehicle():
    return Person('Vladya', attributes={'age': 25, 'job': 'influencer', 'gender': 'female'},
                  vehicle=Vehicle('Vladya'))


@pytest.fixture()
def another_person_with_default_vehicle():
    return Person('Stevie',
                  attributes={'age': 36, 'job': 'blue_collar_crime', 'gender': 'male'},
                  vehicle=Vehicle('Stevie'))


@pytest.fixture()
def person_with_electric_vehicle():
    return Person('Eddy', attributes={'age': 45, 'job': 'white_collar_crime', 'gender': 'male'},
                  vehicle=ElectricVehicle('Eddy'))


@pytest.fixture()
def population_without_vehicles(person_without_a_vehicle):
    pop = Population()
    hhld = Household(hid='1')
    hhld.add(person_without_a_vehicle)
    pop.add(hhld)
    return pop


@pytest.fixture()
def population_with_default_vehicles(population_without_vehicles, person_with_default_vehicle,
                                     another_person_with_default_vehicle):
    hhld = Household(hid='2')
    hhld.add(person_with_default_vehicle)
    hhld.add(another_person_with_default_vehicle)
    population_without_vehicles.add(hhld)
    return population_without_vehicles


@pytest.fixture()
def population_with_electric_vehicles(population_with_default_vehicles, person_with_electric_vehicle):
    hhld = Household(hid='3')
    hhld.add(person_with_electric_vehicle)
    population_with_default_vehicles.add(hhld)
    return population_with_default_vehicles


def test_population_without_vehicles_does_not_have_vehicles(population_without_vehicles):
    assert not population_without_vehicles.has_vehicles


def test_population_with_default_vehicles_has_vehicles(population_with_default_vehicles):
    assert population_with_default_vehicles.has_vehicles


def test_population_with_electric_vehicles_has_vehicles(population_with_electric_vehicles):
    assert population_with_electric_vehicles.has_vehicles


def test_extracting_vehicles_from_population(population_with_electric_vehicles):
    pop_vehicles = population_with_electric_vehicles.vehicles()
    assert pop_vehicles == {
        Vehicle('Vladya'),
        Vehicle('Stevie'),
        ElectricVehicle('Eddy')
    }

def test_extracting_vehicle_types_from_population(population_with_electric_vehicles):
    pop_vehicle_types = population_with_electric_vehicles.vehicle_types()
    assert pop_vehicle_types == {
        VehicleType('defaultVehicleType'),
        VehicleType('defaultElectricVehicleType')
    }
