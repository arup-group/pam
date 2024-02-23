import os
from copy import deepcopy

import geopandas as gp
import pytest
from pam.activity import Activity, Leg, Plan
from pam.core import Household, Person, Population
from pam.operations import cropping
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from shapely.geometry import Point, Polygon


@pytest.fixture
def test_plan() -> Plan:
    plan = Plan()
    plan.day = [
        Activity(seq=1, act="home", loc=Point(0.31, 0.81), start_time=mtdt(0), end_time=mtdt(420)),
        Leg(
            seq=1,
            mode="car",
            start_loc=Point(0.31, 0.81),
            end_loc=Point(0.12, 1.45),
            start_time=mtdt(420),
            end_time=mtdt(480),
            distance=1000,
        ),
        Activity(
            seq=2, act="shop", loc=Point(0.12, 1.45), start_time=mtdt(480), end_time=mtdt(510)
        ),
        Leg(
            seq=2,
            mode="car",
            start_loc=Point(0.12, 1.45),
            end_loc=Point(0.84, 2.12),
            start_time=mtdt(510),
            end_time=mtdt(540),
            distance=1000,
        ),
        Activity(
            seq=3, act="work", loc=Point(0.84, 2.12), start_time=mtdt(540), end_time=mtdt(800)
        ),
        Leg(
            seq=3,
            mode="walk",
            start_loc=Point(0.84, 2.12),
            end_loc=Point(1.90, 0.23),
            start_time=mtdt(800),
            end_time=mtdt(900),
            distance=1000,
        ),
        Activity(
            seq=4, act="medical", loc=Point(1.90, 0.23), start_time=mtdt(900), end_time=mtdt(960)
        ),
        Leg(
            seq=4,
            mode="walk",
            start_loc=Point(1.90, 0.23),
            end_loc=Point(2.26, 0.24),
            start_time=mtdt(960),
            end_time=mtdt(990),
            distance=1000,
        ),
        Activity(
            seq=5, act="other", loc=Point(2.26, 0.24), start_time=mtdt(990), end_time=mtdt(1010)
        ),
        Leg(
            seq=5,
            mode="walk",
            start_loc=Point(2.26, 0.24),
            end_loc=Point(2.77, 1.82),
            start_time=mtdt(1010),
            end_time=mtdt(1030),
            distance=1000,
        ),
        Activity(
            seq=6, act="other", loc=Point(2.77, 1.82), start_time=mtdt(1030), end_time=mtdt(1060)
        ),
        Leg(
            seq=6,
            mode="walk",
            start_loc=Point(2.77, 1.82),
            end_loc=Point(1.88, 1.72),
            start_time=mtdt(1060),
            end_time=mtdt(1100),
            distance=1000,
        ),
        Activity(
            seq=7, act="other", loc=Point(1.88, 1.72), start_time=mtdt(1100), end_time=mtdt(1200)
        ),
        Leg(
            seq=7,
            mode="car",
            start_loc=Point(1.88, 1.72),
            end_loc=Point(0.23, 0.10),
            start_time=mtdt(1200),
            end_time=mtdt(1210),
            distance=1000,
        ),
        Activity(
            seq=8, act="home", loc=Point(0.23, 0.10), start_time=mtdt(1210), end_time=END_OF_DAY
        ),
    ]
    return plan


@pytest.fixture
def test_population(test_plan) -> Population:
    hh = Household(1, loc=Point(0.31, 0.81))
    population = Population()
    person = Person(1)
    person.plan = test_plan
    hh.add(person)
    population.add(hh)

    return population


@pytest.fixture
def test_zoning_system() -> gp.GeoDataFrame:
    """Dummy orthogonal zoning system."""
    zones = []
    labels = [chr(x) for x in range(97, 106)]
    for x in range(3):
        for y in range(3):
            zones.append(Polygon([(x, y), (x, y + 1), (x + 1, y + 1), (x + 1, y)]))
    zones_gdf = gp.GeoDataFrame({"zone": labels}, geometry=zones)
    zones_gdf.index = zones_gdf.zone

    return zones_gdf


@pytest.fixture
def path_test_plan():
    return os.path.join("tests", "test_data", "test_matsim_plansv12.xml")


@pytest.fixture
def path_boundary():
    return os.path.join("tests", "test_data", "test_geometry.geojson")


@pytest.fixture
def path_output_dir():
    return os.path.join("tests", "test_data", "output", "cropped")


def get_activity_zones(plan: Plan, zoning_system: gp.GeoDataFrame) -> set:
    """Return the activity location zones."""
    locs = gp.GeoDataFrame(geometry=[x.location.loc for x in plan.activities])
    return list(locs.sjoin(zoning_system).zone)


def test_simple_cropping(test_plan, test_zoning_system):
    """Only keep legs entering/exiting zone h."""
    boundary = test_zoning_system.loc["h"].geometry
    plan_cropped = deepcopy(test_plan)
    cropping.simplify_external_plans(plan_cropped, boundary)
    activity_zones = get_activity_zones(plan_cropped, test_zoning_system)
    assert activity_zones == ["g", "h", "e"]


@pytest.mark.filterwarnings("ignore:invalid value encountered in intersects:RuntimeWarning")
def test_complex_cropping(test_plan, test_zoning_system):
    """Through-trips and multiple entries to the core area (e)."""
    boundary = test_zoning_system.loc["e"].geometry
    plan_cropped = deepcopy(test_plan)
    cropping.simplify_external_plans(plan_cropped, boundary)
    activity_zones = get_activity_zones(plan_cropped, test_zoning_system)
    assert activity_zones == ["c", "d", "h", "e", "a"]


def test_fully_external(test_plan, test_zoning_system, test_population):
    """All activities happen outside the core area (i)."""
    boundary = test_zoning_system.loc["i"].geometry
    plan_cropped = deepcopy(test_plan)
    cropping.simplify_external_plans(plan_cropped, boundary)
    assert len(plan_cropped) == 1
    assert list(plan_cropped.activities)[0].act == "external"

    # agents with fully external plans are dropped:
    population_cropped = deepcopy(test_population)
    cropping.simplify_population(population_cropped, boundary)
    assert len(population_cropped) == 0


def test_fully_internal_plan(test_plan, test_zoning_system):
    """All activities in spatial scope -> no change of agent plans."""
    boundary = test_zoning_system.dissolve().geometry[0]
    plan_cropped = deepcopy(test_plan)
    cropping.simplify_external_plans(plan_cropped, boundary)
    assert len(test_plan) == len(plan_cropped)
