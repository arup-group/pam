import pandas as pd
import pytest
from pam.read import load_travel_diary

test_trips_path = pytest.test_data_dir / "simple_travel_diaries.csv"
test_attributes_path = pytest.test_data_dir / "simple_persons_data.csv"


@pytest.fixture
def test_trips():
    df = pd.read_csv(test_trips_path)
    assert not df.empty
    return df


@pytest.fixture
def test_attributes():
    df = pd.read_csv(test_attributes_path)
    assert not df.empty
    return df


def test_agent_pid_5_not_start_from_home(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[2].people[5].activities]
    assert acts == ["work", "home"]


def test_agent_pid_6_not_return_home(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[3].people[6].activities]
    assert acts == ["home", "work"]


def test_agent_pid_7_not_start_and_return_home_night_worker(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    population[4][7]
    acts = [a.act for a in population.households[4].people[7].activities]
    assert acts == ["work", "home", "work"]


def test_agent_pid_8_not_start_and_return_home_night_worker_complex_chain_type1(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[5].people[8].activities]
    assert acts == ["work", "shop", "home", "work"]


def test_agent_pid_9_not_start_and_return_home_night_worker_complex_chain_type2(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[6].people[9].activities]
    assert acts == ["work", "shop", "home", "work"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_10_not_start_from_home_impossible_chain_type1(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[7].people[10].activities]
    assert acts == ["work", "shop", "home"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_11_not_start_from_home_impossible_chain_type2(test_trips, test_attributes):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[8].people[11].activities]
    assert acts == ["work", "shop", "home"]


def test_agent_pid_12_not_start_and_return_home_night_worker_complex_chain_type1_intra_trip(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[9].people[12].activities]
    assert acts == ["work", "shop", "home", "work"]


def test_agent_pid_13_not_start_and_return_home_night_worker_complex_chain_type2_intra_trip(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[10].people[13].activities]
    assert acts == ["work", "shop", "home", "work"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_14_not_start_from_home_impossible_chain_type1_intra_trip(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[11].people[14].activities]
    assert acts == ["work", "shop", "home"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_15_not_start_from_home_impossible_chain_type2_intra_trip(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[12].people[15].activities]
    assert acts == ["work", "shop", "home"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_16_not_start_and_return_home_night_worker_complex_chain_type1_not_work(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[13].people[16].activities]
    assert acts == ["work", "shop", "home", "work"]


def test_agent_pid_17_not_start_and_return_home_night_worker_complex_chain_type2_not_work(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[14].people[17].activities]
    assert acts == ["other", "shop", "home", "other"]


@pytest.mark.skip(reason="Redundant test - we rarely see this requirment any more")
def test_agent_pid_18_not_start_from_home_impossible_chain_type1_not_work(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[15].people[18].activities]
    assert acts == ["other", "shop", "home"]


def test_agent_pid_19_not_start_and_return_home_night_worker_complex_chain_type1_intra_trip_not_work(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[16].people[19].activities]
    assert acts == ["escort", "shop", "home", "escort"]


def test_agent_pid_20_not_start_and_return_home_night_worker_complex_chain_type2_intra_trip_not_work(
    test_trips, test_attributes
):
    population = load_travel_diary(test_trips, test_attributes)
    acts = [a.act for a in population.households[17].people[20].activities]
    assert acts == ["escort", "shop", "home", "escort"]
