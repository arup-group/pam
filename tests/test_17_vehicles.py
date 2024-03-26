from copy import deepcopy

import importlib_resources
import lxml
import pytest
from pam import PAMVehicleIdError, PAMVehicleTypeError
from pam.core import Person, Population
from pam.read.matsim import read_matsim
from pam.vehicles import ElectricVehicle, Vehicle, VehicleManager, VehicleType
from pam.write.matsim import write_matsim


@pytest.fixture()
def car_type():
    return VehicleType("car")


@pytest.fixture()
def lorry_type():
    return VehicleType("lorry", passengerCarEquivalents=3.0)


def test_veh_manager_add_type(car_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    assert "car" in manager._veh_types


def test_veh_manager_add_type_again(car_type, lorry_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    manager.add_type(lorry_type)
    manager.add_type(car_type)
    assert "car" in manager._veh_types


def test_veh_manager_remove_type(car_type, lorry_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    manager.add_type(lorry_type)
    manager.remove_type("lorry")
    assert "lorry" not in manager._veh_types


def test_veh_manager_remove_missing_type(car_type, lorry_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    with pytest.raises(PAMVehicleTypeError):
        manager.remove_type("lorry")


def test_create_car():
    veh = Vehicle("0", "car")
    assert veh.type_id == "car"


def test_create_ev():
    veh = ElectricVehicle("0", "car")
    assert veh.type_id == "car"


def test_add_veh_failure_due_to_unknown_type():
    manager = VehicleManager()
    veh1 = Vehicle("1", "car")
    with pytest.raises(PAMVehicleTypeError):
        manager.add_veh(veh1)


def test_add_veh(car_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    veh1 = Vehicle("1", "car")
    manager.add_veh(veh1)
    assert "1" in manager


def test_add_ev_failure_due_to_unknown_type():
    manager = VehicleManager()
    veh1 = ElectricVehicle("1", "car")
    with pytest.raises(PAMVehicleTypeError):
        manager.add_veh(veh1)


def test_add_ev(car_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    veh1 = ElectricVehicle("1", "car")
    manager.add_veh(veh1)
    assert "1" in manager


def test_set_veh_fails_due_to_unknown_type():
    manager = VehicleManager()
    with pytest.raises(UserWarning):
        manager["1"] = "vehicle1"


def test_set_veh_fails_due_to_missing_type():
    manager = VehicleManager()
    veh1 = Vehicle("1", "car")
    with pytest.raises(PAMVehicleTypeError):
        manager["1"] = veh1


def test_set_veh(car_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    veh1 = Vehicle("1", "car")
    manager["1"] = veh1
    assert "1" in manager


def test_set_ev(car_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    veh1 = ElectricVehicle("1", "car")
    manager["1"] = veh1
    assert "1" in manager


@pytest.fixture()
def manager(car_type, lorry_type):
    manager = VehicleManager()
    manager.add_type(car_type)
    manager.add_type(lorry_type)
    for i in range(2):
        veh = Vehicle(f"car_{i}", "car")
        manager[f"car_{i}"] = veh
    for i in range(2):
        veh = ElectricVehicle(f"ev_{i}", "car")
        manager[f"ev_{i}"] = veh
    for i in range(1):
        veh = Vehicle(f"freight_{i}", "lorry")
        manager[f"freight_{i}"] = veh
    return manager


def test_get_veh(manager):
    assert isinstance(manager.get("car_0"), Vehicle)
    assert manager.get("car_0").type_id == "car"

    assert isinstance(manager.get("ev_0"), ElectricVehicle)
    assert manager.get("ev_0").type_id == "car"

    assert isinstance(manager.get("freight_0"), Vehicle)
    assert manager.get("freight_0").type_id == "lorry"

    assert isinstance(manager["car_0"], Vehicle)
    assert manager["car_0"].type_id == "car"

    assert isinstance(manager["ev_0"], ElectricVehicle)
    assert manager["ev_0"].type_id == "car"

    assert isinstance(manager["freight_0"], Vehicle)
    assert manager["freight_0"].type_id == "lorry"

    with pytest.raises(KeyError):
        manager["0"]


def test_manager_contains(manager):
    assert "0" not in manager
    assert "car_0" in manager


def test_manager_equals(manager):
    assert manager == manager
    other1 = VehicleManager()
    assert manager != other1
    other2 = deepcopy(manager)
    other2._vehicles["new"] = Vehicle("new", "new")
    assert manager != other2


def test_clear_types(manager):
    manager.clear_types()
    assert manager._veh_types == {}


def test_manager_length(manager):
    assert manager.len() == 5


def test_manager_iters(manager):
    assert set([k for k, v in manager._veh_types.items()]) == {"car", "lorry"}
    assert set([k for k, v in manager._vehicles.items()]) == {
        "car_0",
        "car_1",
        "freight_0",
        "ev_0",
        "ev_1",
    }
    assert set([k for k, v in manager.evs.items()]) == {"ev_0", "ev_1"}


@pytest.fixture
def vehicles_v2_xsd():
    xsd_path = importlib_resources.files("pam") / "fixtures" / "dtd" / "vehicleDefinitions_v2.0.xsd"
    xml_schema_doc = lxml.etree.parse(xsd_path)
    yield lxml.etree.XMLSchema(xml_schema_doc)


def test_ev_charger_types(manager):
    assert manager.charger_types() == {"default"}


@pytest.fixture
def electric_vehicles_v1_dtd():
    dtd_path = importlib_resources.files("pam") / "fixtures" / "dtd" / "electric_vehicles_v1.dtd"
    yield lxml.etree.DTD(dtd_path)


def test_manager_is_consistent(manager):
    assert manager.is_consistent()


def test_manager_inconsistent_vehs(manager):
    manager._vehicles["taxi_0"] = Vehicle("taxi_0", "taxi")
    with pytest.raises(PAMVehicleIdError):
        manager.is_consistent()


def test_manager_redundant_veh_types(manager):
    manager._veh_types["taxi"] = VehicleType("taxi")
    assert manager.redundant_types() == {"taxi": VehicleType("taxi")}


def test_raise_when_read_evs_but_no_vehs(electric_vehicles_xml_path):
    with pytest.raises(UserWarning):
        manager = VehicleManager()
        manager.from_xml(vehs_path=None, evs_path=electric_vehicles_xml_path)


def test_reading_all_vehicles_file(all_vehicle_xml_path):
    manager = VehicleManager()
    manager.from_xml(all_vehicle_xml_path)
    assert manager._veh_types == {
        "defaultVehicleType": VehicleType("defaultVehicleType"),
        "defaultElectricVehicleType": VehicleType("defaultElectricVehicleType"),
    }
    assert manager._vehicles == {
        "Eddy": Vehicle("Eddy", "defaultElectricVehicleType"),
        "Stevie": Vehicle("Stevie", "defaultVehicleType"),
        "Vladya": Vehicle("Vladya", "defaultVehicleType"),
    }


def test_reading_electric_vehicles(all_vehicle_xml_path, electric_vehicles_xml_path):
    manager = VehicleManager()
    manager.from_xml(all_vehicle_xml_path, electric_vehicles_xml_path)
    assert manager._veh_types == {
        "defaultVehicleType": VehicleType("defaultVehicleType"),
        "defaultElectricVehicleType": VehicleType("defaultElectricVehicleType"),
    }
    assert manager._vehicles == {
        "Eddy": ElectricVehicle("Eddy", "defaultElectricVehicleType"),
        "Stevie": Vehicle("Stevie", "defaultVehicleType"),
        "Vladya": Vehicle("Vladya", "defaultVehicleType"),
    }


def test_assign_vehicles_to_person(manager):
    person = Person("0", attributes={"subpopulation": "default", "vehicles": {"car": "car_0"}})
    person.assign_vehicles_from_manager(manager)
    assert "car_0" not in manager
    assert person.vehicles == {"car": Vehicle("car_0", "car")}


def test_assign_evs_to_person(manager):
    person = Person("0", attributes={"subpopulation": "default", "vehicles": {"car": "ev_0"}})
    person.assign_vehicles_from_manager(manager)
    assert "ev_0" not in manager
    assert person.vehicles == {"car": ElectricVehicle("ev_0", "car")}


def test_assign_multiple_vehs_to_person(manager):
    person = Person(
        "0", attributes={"subpopulation": "default", "vehicles": {"ev": "ev_0", "car": "car_0"}}
    )
    person.assign_vehicles_from_manager(manager)
    assert "car_0" not in manager
    assert "ev_0" not in manager
    assert person.vehicles["ev"] == ElectricVehicle("ev_0", "car")
    assert person.vehicles["car"] == Vehicle("car_0", "car")


def test_rebuild_manager_fails_due_to_missing_type():
    population = Population()
    population._vehicles_manager = VehicleManager()
    population._vehicles_manager.add_type(VehicleType("car"))

    person = Person("0", attributes={"subpopulation": "default"})
    person.vehicles = {"big_car": Vehicle("0", "big_car")}
    population.add(person)

    with pytest.raises(PAMVehicleIdError):
        population.rebuild_vehicles_manager()


def test_rebuild_manager_fails_due_to_duplicates():
    population = Population()
    population._vehicles_manager = VehicleManager()
    population._vehicles_manager.add_type(VehicleType("car"))

    personA = Person("0", attributes={"subpopulation": "default"})
    personA.vehicles = {"car0": Vehicle("car0", "car")}
    personB = Person("1", attributes={"subpopulation": "default"})
    personB.vehicles = {"car0": Vehicle("car0", "car")}
    population.add(personA)
    population.add(personB)

    with pytest.raises(PAMVehicleIdError):
        population.rebuild_vehicles_manager()


def test_rebuild_manager_single_agent(manager):
    population = Population()
    population._vehicles_manager = manager

    person = Person("0", attributes={"subpopulation": "default"})
    person.vehicles = {"car": Vehicle("0", "car")}
    population.add(person)

    population.rebuild_vehicles_manager()
    assert population._vehicles_manager._vehicles == {"0": Vehicle("0", "car")}
    assert population._vehicles_manager.redundant_types() == {
        "lorry": VehicleType("lorry", passengerCarEquivalents=3.0)
    }


def test_rebuild_manager_multi_agent(manager):
    population = Population()
    population._vehicles_manager = manager

    personA = Person("0", attributes={"subpopulation": "default"})
    personA.vehicles = {"0": Vehicle("0", "car")}
    population.add(personA)

    personB = Person("1", attributes={"subpopulation": "freight"})
    personB.vehicles = {"1": Vehicle("1", "lorry")}
    population.add(personB)

    personC = Person("2", attributes={"subpopulation": "ev"})
    personC.vehicles = {"2": ElectricVehicle("2", "car")}
    population.add(personC)

    population.rebuild_vehicles_manager()
    assert population._vehicles_manager._vehicles == {
        "0": Vehicle("0", "car"),
        "1": Vehicle("1", "lorry"),
        "2": ElectricVehicle("2", "car"),
    }
    assert population._vehicles_manager.redundant_types() == {}


def test_writing_all_vehicles_results_in_valid_xml_file(manager, tmp_path, vehicles_v2_xsd):
    file_path = tmp_path / "all_vehicles.xml"
    manager.to_xml(vehs_path=file_path)
    xml_obj = lxml.etree.parse(file_path)
    vehicles_v2_xsd.assertValid(xml_obj)  # this needs internet?


def test_writing_electric_vehicles_results_in_valid_xml_file(
    manager, tmp_path, electric_vehicles_v1_dtd
):
    vehs_path = tmp_path / "all_vehicles.xml"
    evs_path = tmp_path / "ev_vehicles.xml"
    manager.to_xml(vehs_path=vehs_path, evs_path=evs_path)
    xml_obj = lxml.etree.parse(evs_path)
    assert electric_vehicles_v1_dtd.validate(xml_obj), (
        f"Doc generated at {evs_path} is not valid against DTD "
        f"due to {electric_vehicles_v1_dtd.error_log.filter_from_errors()}"
    )


@pytest.fixture
def ev_population_xml_path():
    return pytest.test_data_dir / "vehicles" / "ev_population.xml"


@pytest.fixture
def all_vehicle_xml_path():
    return pytest.test_data_dir / "vehicles" / "all_vehicles.xml"


def test_read_write_xml_consistently(all_vehicle_xml_path, electric_vehicles_xml_path, tmp_path):
    manager = VehicleManager()
    manager.from_xml(all_vehicle_xml_path, electric_vehicles_xml_path)
    vehs_path = tmp_path / "vehs.xml"
    evs_path = tmp_path / "evs.xml"
    manager.to_xml(vehs_path, evs_path)
    duplicate = VehicleManager()
    duplicate.from_xml(vehs_path, evs_path)
    assert manager == duplicate


def test_read_vehs_into_population(
    ev_population_xml_path, all_vehicle_xml_path, electric_vehicles_xml_path
):
    population = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        electric_vehicles_path=electric_vehicles_xml_path,
    )
    assert population._vehicles_manager._veh_types == {
        "defaultVehicleType": VehicleType("defaultVehicleType"),
        "defaultElectricVehicleType": VehicleType("defaultElectricVehicleType"),
    }
    assert population._vehicles_manager._vehicles == {}

    # check vehicles attribute is removed
    for pid in ["Eddy", "Stevie", "Vladya"]:
        assert list(population[pid][pid].attributes.keys()) == ["subpopulation"]

    assert population["Eddy"]["Eddy"].vehicles["car"] == ElectricVehicle(
        "Eddy", "defaultElectricVehicleType"
    )
    assert population["Stevie"]["Stevie"].vehicles["car"] == Vehicle("Stevie", "defaultVehicleType")
    assert population["Vladya"]["Vladya"].vehicles["car"] == Vehicle("Vladya", "defaultVehicleType")


def test_write_vehs_into_population(
    ev_population_xml_path, all_vehicle_xml_path, electric_vehicles_xml_path, tmp_path
):
    population = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        electric_vehicles_path=electric_vehicles_xml_path,
    )
    plans_path = tmp_path / "plans.xml"
    vehs_path = tmp_path / "vehs.xml"
    evs_path = tmp_path / "evs.xml"
    write_matsim(population, plans_path=plans_path, vehs_path=vehs_path, evs_path=evs_path)
    duplicate = read_matsim(
        plans_path=plans_path, all_vehicles_path=vehs_path, electric_vehicles_path=evs_path
    )
    assert population == duplicate


def test_read_edit_size_write(
    ev_population_xml_path, all_vehicle_xml_path, electric_vehicles_xml_path, tmp_path
):
    population = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        electric_vehicles_path=electric_vehicles_xml_path,
    )
    population._vehicles_manager._veh_types[
        "defaultElectricVehicleType"
    ].passengerCarEquivalents = 1.2
    plans_path = tmp_path / "plans.xml"
    vehs_path = tmp_path / "vehs.xml"
    evs_path = tmp_path / "evs.xml"
    write_matsim(population, plans_path=plans_path, vehs_path=vehs_path, evs_path=evs_path)
    duplicate = read_matsim(
        plans_path=plans_path, all_vehicles_path=vehs_path, electric_vehicles_path=evs_path
    )
    assert (
        duplicate._vehicles_manager._veh_types["defaultElectricVehicleType"].passengerCarEquivalents
        == 1.2
    )


def test_read_edit_veh_write(
    ev_population_xml_path, all_vehicle_xml_path, electric_vehicles_xml_path, tmp_path
):
    population = read_matsim(
        plans_path=ev_population_xml_path,
        all_vehicles_path=all_vehicle_xml_path,
        electric_vehicles_path=electric_vehicles_xml_path,
    )
    population["Stevie"]["Stevie"].vehicles["car"] = ElectricVehicle(
        "Stevie", "defaultElectricVehicleType"
    )
    population["Eddy"]["Eddy"].vehicles["car"] = Vehicle("Eddy", "defaultVehicleType")

    plans_path = tmp_path / "plans.xml"
    vehs_path = tmp_path / "vehs.xml"
    evs_path = tmp_path / "evs.xml"
    write_matsim(population, plans_path=plans_path, vehs_path=vehs_path, evs_path=evs_path)
    duplicate = read_matsim(
        plans_path=plans_path, all_vehicles_path=vehs_path, electric_vehicles_path=evs_path
    )
    assert duplicate["Stevie"]["Stevie"].vehicles["car"] == ElectricVehicle(
        "Stevie", "defaultElectricVehicleType"
    )
    assert duplicate["Eddy"]["Eddy"].vehicles["car"] == Vehicle("Eddy", "defaultVehicleType")


def test_population_vehicles_types(manager):
    population = Population()
    population._vehicles_manager = manager
    assert set(population.vehicle_types.keys()) == {"car", "lorry"}


def test_iter_evs(car_type):
    population = Population()
    population.add_veh_type(car_type)
    for i in range(2):
        person = Person(i)
        person.vehicles = {"car": ElectricVehicle(f"car_{i}", "car")}
        population.add(person)
    for i in range(2, 4):
        person = Person(i)
        person.vehicles = {"car": Vehicle(f"car_{i}", "car")}
        population.add(person)
    population._vehicles_manager = manager
    assert list(population.evs()) == [
        (0, 0, "car", ElectricVehicle("car_0", "car")),
        (1, 1, "car", ElectricVehicle("car_1", "car")),
    ]


def test_population_has_vehs(manager):
    population = Population()
    population.add(Person(0))
    assert not population.has_vehicles
    population.add(Person(0, vehicles={"car": Vehicle("0", "car")}))
    assert not population.has_electric_vehicles
    assert population.has_vehicles
    population.add(Person(1, vehicles={"car": ElectricVehicle("1", "car")}))
    assert population.has_electric_vehicles


def test_add_veh_to_agent_fail_due_to_missing_type(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    with pytest.raises(UserWarning):
        population.add_veh(0, 0, "car", Vehicle("0", "truck"))


def test_add_veh_to_agent_fails_due_to_duplicate(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    population.add_veh(0, 0, "car", Vehicle("0", "car"))
    with pytest.raises(UserWarning):
        population.add_veh(0, 0, "taxi", Vehicle("0", "car"))


def test_add_veh_to_agent_ok(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    population.add_veh(0, 0, "car", Vehicle("0", "car"))
    assert population[0][0].vehicles["car"] == Vehicle("0", "car")


def test_add_veh_to_agent_ok_with_overwrite(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    population.add_veh(0, 0, "car", Vehicle("0", "car"))
    population.add_veh(0, 0, "car", Vehicle("0", "lorry"))
    assert population[0][0].vehicles["car"] == Vehicle("0", "lorry")


def test_population_check_vehicles(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    population.add_veh(0, 0, "car", Vehicle("0", "car"))
    assert population.check_vehicles()
    population[0][0].vehicles["car"] = Vehicle("0", "flying_car")
    with pytest.raises(PAMVehicleIdError):
        population.check_vehicles()


def test_update_vehicles_manager(manager):
    population = Population()
    population.add(Person(0))
    population._vehicles_manager = manager
    population.add_veh(0, 0, "car", Vehicle("0", "car"))
    population.update_vehicles_manager()
    population[0][0].vehicles["car"] = Vehicle("0", "flying_car")
    with pytest.raises(PAMVehicleIdError):
        population.update_vehicles_manager()
