import pytest
import lxml
import os
import logging
from pam.core import Person, Population, Household
from pam.vehicle import Vehicle, ElectricVehicle, VehicleType
from pam import PAMVehicleIdError
from pam.write import write_vehicles, write_all_vehicles, write_electric_vehicles
from pam.read import read_matsim, read_all_vehicles_file, read_electric_vehicles_file


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


def test_population_with_default_vehicles_does_not_have_electric_vehicles(population_with_default_vehicles):
    assert not population_with_default_vehicles.has_electric_vehicles


def test_population_with_electric_vehicles_has_vehicles(population_with_electric_vehicles):
    assert population_with_electric_vehicles.has_vehicles


def test_population_with_electric_vehicles_has_electric_vehicles(population_with_electric_vehicles):
    assert population_with_electric_vehicles.has_electric_vehicles


def test_extracting_vehicles_from_population(population_with_electric_vehicles):
    assert population_with_electric_vehicles.vehicles() == {
        Vehicle('Vladya'),
        Vehicle('Stevie'),
        ElectricVehicle('Eddy')
    }


def test_sorting_vehicles_list(population_with_electric_vehicles):
    pop_vehicles = list(population_with_electric_vehicles.vehicles())
    pop_vehicles.sort()
    assert pop_vehicles == [
        ElectricVehicle('Eddy'),
        Vehicle('Stevie'),
        Vehicle('Vladya')
    ]


def test_extracting_electric_vehicles_from_population(population_with_electric_vehicles):
    assert population_with_electric_vehicles.electric_vehicles() == {
        ElectricVehicle('Eddy')
    }


def test_extracting_vehicle_types_from_population(population_with_electric_vehicles):
    assert population_with_electric_vehicles.vehicle_types() == {
        VehicleType('defaultVehicleType'),
        VehicleType('defaultElectricVehicleType')
    }


def test_population_with_electric_vehicles_has_uniquely_defined_vehicle_types(population_with_electric_vehicles):
    assert population_with_electric_vehicles.has_uniquely_indexed_vehicle_types


def test_population_with_non_uniquely_defined_vehicle_types(population_with_electric_vehicles):
    hhld = Household(hid='4')
    hhld.add(Person('Micky Faraday',
                    vehicle=ElectricVehicle(charger_types='other,tesla', id='Micky Faraday',
                                            vehicle_type=VehicleType('defaultElectricVehicleType', networkMode='e_car')
                                            )))
    population_with_electric_vehicles.add(hhld)
    assert population_with_electric_vehicles.vehicle_types() == {
        VehicleType('defaultVehicleType'),
        VehicleType('defaultElectricVehicleType'),
        VehicleType('defaultElectricVehicleType', networkMode='e_car')
    }
    assert not population_with_electric_vehicles.has_uniquely_indexed_vehicle_types


def test_extracting_unique_electric_charger_types_from_population(population_with_electric_vehicles):
    hhld = Household(hid='4')
    hhld.add(Person('Micky Faraday',
                    vehicle=ElectricVehicle(charger_types='other,tesla', id='Micky Faraday')))
    population_with_electric_vehicles.add(hhld)

    assert population_with_electric_vehicles.electric_vehicle_charger_types() == {'default', 'other', 'tesla'}


@pytest.fixture
def vehicles_v2_xsd():
    xsd_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'pam', "fixtures", "dtd", "vehicleDefinitions_v2.0.xsd"))
    xml_schema_doc = lxml.etree.parse(xsd_path)
    yield lxml.etree.XMLSchema(xml_schema_doc)


@pytest.fixture
def electric_vehicles_v1_dtd():
    dtd_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'pam', "fixtures", "dtd", "electric_vehicles_v1.dtd"))
    yield lxml.etree.DTD(dtd_path)


def test_writing_all_vehicles_results_in_valid_xml_file(tmpdir, population_with_electric_vehicles, vehicles_v2_xsd):
    write_all_vehicles(tmpdir, population_with_electric_vehicles.vehicles(),
                       population_with_electric_vehicles.vehicle_types())

    generated_file_path = os.path.join(tmpdir, 'all_vehicles.xml')
    xml_obj = lxml.etree.parse(generated_file_path)
    vehicles_v2_xsd.assertValid(xml_obj)


def test_generates_matsim_vehicles_xml_file_containing_expected_vehicle_types(tmpdir,
                                                                              population_with_electric_vehicles):
    expected_vehicle_types = {'defaultVehicleType', 'defaultElectricVehicleType'}

    write_all_vehicles(tmpdir, population_with_electric_vehicles.vehicles(),
                       population_with_electric_vehicles.vehicle_types())

    generated_file_path = os.path.join(tmpdir, 'all_vehicles.xml')
    xml_obj = lxml.etree.parse(generated_file_path)

    vehicle_types = xml_obj.findall('{http://www.matsim.org/files/dtd}vehicleType')
    vehicle_types = set(vehicle_type.get('id') for vehicle_type in vehicle_types)
    assert expected_vehicle_types == vehicle_types


def test_generates_matsim_vehicles_xml_file_containing_expected_vehicles(tmpdir, population_with_electric_vehicles):
    expected_vehicles = {
        'Eddy': 'defaultElectricVehicleType',
        'Stevie': 'defaultVehicleType',
        'Vladya': 'defaultVehicleType'
    }

    write_all_vehicles(tmpdir, population_with_electric_vehicles.vehicles(),
                       population_with_electric_vehicles.vehicle_types())

    generated_file_path = os.path.join(tmpdir, 'all_vehicles.xml')
    xml_obj = lxml.etree.parse(generated_file_path)

    vehicles = xml_obj.findall('{http://www.matsim.org/files/dtd}vehicle')
    assert expected_vehicles == {vehicle.get('id'): vehicle.get('type') for vehicle in vehicles}


def test_writing_electric_vehicles_results_in_valid_xml_file(tmpdir, population_with_electric_vehicles,
                                                             electric_vehicles_v1_dtd):
    write_electric_vehicles(tmpdir, population_with_electric_vehicles.electric_vehicles())

    generated_file_path = os.path.join(tmpdir, 'electric_vehicles.xml')
    xml_obj = lxml.etree.parse(generated_file_path)
    assert electric_vehicles_v1_dtd.validate(xml_obj), \
        f'Doc generated at {generated_file_path} is not valid against DTD ' \
        f'due to {electric_vehicles_v1_dtd.error_log.filter_from_errors()}'


def test_generates_electric_vehicles_xml_file_containing_expected_vehicles(tmpdir, population_with_electric_vehicles):
    expected_vehicles = [
        {'id': 'Eddy', 'battery_capacity': '60', 'initial_soc': '60', 'charger_types': 'default',
         'vehicle_type': 'defaultElectricVehicleType'}
    ]

    write_electric_vehicles(tmpdir, population_with_electric_vehicles.electric_vehicles())

    generated_file_path = os.path.join(tmpdir, 'electric_vehicles.xml')
    xml_obj = lxml.etree.parse(generated_file_path)

    vehicles = xml_obj.findall('vehicle')
    assert expected_vehicles == [v.attrib for v in vehicles]


def test_generating_vehicle_files_from_nonelectric_population_produces_only_vehicle_file(
        tmpdir, population_with_default_vehicles):
    expected_all_vehicles_file = os.path.join(tmpdir, 'all_vehicles.xml')
    expected_electric_vehicles_file = os.path.join(tmpdir, 'electric_vehicles.xml')

    assert not os.path.exists(expected_all_vehicles_file)
    assert not os.path.exists(expected_electric_vehicles_file)

    write_vehicles(tmpdir, population_with_default_vehicles)

    assert os.path.exists(expected_all_vehicles_file)
    assert not os.path.exists(expected_electric_vehicles_file)


def test_generating_vehicle_files_from_electric_population_produces_both_files(tmpdir,
                                                                               population_with_electric_vehicles):
    expected_all_vehicles_file = os.path.join(tmpdir, 'all_vehicles.xml')
    expected_electric_vehicles_file = os.path.join(tmpdir, 'electric_vehicles.xml')

    assert not os.path.exists(expected_all_vehicles_file)
    assert not os.path.exists(expected_electric_vehicles_file)

    write_vehicles(tmpdir, population_with_electric_vehicles)

    assert os.path.exists(expected_all_vehicles_file)
    assert os.path.exists(expected_electric_vehicles_file)


def test_generating_vehicle_files_from_electric_population_informs_of_charger_types(tmpdir,
                                                                                    population_with_electric_vehicles,
                                                                                    caplog):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    write_vehicles(tmpdir, population_with_electric_vehicles)

    recs = [rec for rec in caplog.records if 'electric' in rec.message]
    last_electric_message = recs[-1]
    assert last_electric_message.levelname == 'INFO'
    assert 'unique charger types: ' in last_electric_message.message
    assert "{'default'}" in last_electric_message.message


@pytest.fixture
def ev_population_xml_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data", "vehicles", "ev_population.xml"))


@pytest.fixture
def all_vehicle_xml_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data", "vehicles", "all_vehicles.xml"))


@pytest.fixture
def expected_all_vehicle_xml_output():
    return {
        'Eddy': Vehicle('Eddy', VehicleType('defaultElectricVehicleType')),
        'Stevie': Vehicle('Stevie', VehicleType('defaultVehicleType')),
        'Vladya': Vehicle('Vladya', VehicleType('defaultVehicleType'))
    }


@pytest.fixture
def electric_vehicles_xml_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data", "vehicles", "electric_vehicles.xml"))


@pytest.fixture
def expected_electric_vehicle_xml_output():
    return {
        'Eddy': ElectricVehicle('Eddy', VehicleType('defaultElectricVehicleType')),
        'Stevie': Vehicle('Stevie', VehicleType('defaultVehicleType')),
        'Vladya': Vehicle('Vladya', VehicleType('defaultVehicleType'))
    }


def test_reading_all_vehicles_file(all_vehicle_xml_path, expected_all_vehicle_xml_output):
    vehicles = read_all_vehicles_file(all_vehicle_xml_path)
    assert vehicles == expected_all_vehicle_xml_output


def test_reading_electric_vehicles_with_all_vehicles_results_in_vehicles_being_updated_to_electric_vehicle_class(
        electric_vehicles_xml_path, expected_all_vehicle_xml_output, expected_electric_vehicle_xml_output):
    vehicles = read_electric_vehicles_file(electric_vehicles_xml_path, expected_all_vehicle_xml_output)
    assert vehicles == expected_electric_vehicle_xml_output


def test_reading_electric_vehicles_only_results_in_defaulted_vehicle_type(electric_vehicles_xml_path):
    vehicles = read_electric_vehicles_file(electric_vehicles_xml_path)
    assert vehicles == {'Eddy': ElectricVehicle(id='Eddy')}


def test_reading_population_with_both_vehicle_files_assigns_all_vehicles_correctly(
        ev_population_xml_path, all_vehicle_xml_path, electric_vehicles_xml_path, expected_electric_vehicle_xml_output):
    pop = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        electric_vehicles_path=electric_vehicles_xml_path,
        version=12
    )
    for person in ['Eddy', 'Stevie', 'Vladya']:
        pop.get(person).people[person].vehicle = expected_electric_vehicle_xml_output[person]


def test_reading_population_with_all_vehicle_file_defaults_to_vehicle_class(
        ev_population_xml_path, all_vehicle_xml_path, expected_all_vehicle_xml_output):
    pop = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        version=12
    )
    for person in ['Eddy', 'Stevie', 'Vladya']:
        pop.get(person).people[person].vehicle = expected_all_vehicle_xml_output[person]
