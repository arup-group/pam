from io import StringIO

import pandas as pd
import pytest
from pam import PAMValidationLocationsError
from pam.core import Person
from pam.read import build_population, load_travel_diary


@pytest.fixture
def trips():
    trips_csv = StringIO(
        """
pid,hid,seq,hzone,ozone,dzone,purp,mode,tst,tet,freq
0,0,0,Harrow,Harrow,Camden,work,pt,444,473,1
0,0,1,Harrow,Camden,Harrow,home,pt,890,919,2
1,0,0,Harrow,Harrow,Tower Hamlets,work,car,507,528,3
1,0,1,Harrow,Tower Hamlets,Harrow,home,car,1065,1086,4
2,1,0,Islington,Islington,Hackney,shop,pt,422,425,5
2,1,1,Islington,Hackney,Croydon,leisure,walk,485,500,6
2,1,2,Islington,Croydon,Islington,home,pt,560,580,7
"""
    )
    return pd.read_csv(trips_csv)


@pytest.fixture
def activity_encoded_trips():
    trips_csv = StringIO(
        """
pid,hid,seq,hzone,ozone,dzone,oact,dact,mode,tst,tet,freq
0,0,0,Harrow,Harrow,Camden,home,work,pt,444,473,1
0,0,1,Harrow,Camden,Harrow,work,home,pt,890,919,2
1,0,0,Harrow,Harrow,Tower Hamlets,home,work,car,507,528,3
1,0,1,Harrow,Tower Hamlets,Harrow,work,home,car,1065,1086,4
2,1,0,Islington,Islington,Hackney,home,shop,pt,422,425,5
2,1,1,Islington,Hackney,Croydon,shop,leisure,walk,485,500,6
2,1,2,Islington,Croydon,Islington,leisure,home,pt,560,580,7
"""
    )
    return pd.read_csv(trips_csv)


@pytest.fixture
def persons_attributes():
    persons_attributes_csv = StringIO(
        """
pid,hid,hzone,freq,income,age,driver,cats or dogs
0,0,Harrow,1,high,high,yes,dogs
1,0,Harrow,2,low,medium,no,dogs
2,1,Islington,1,medium,low,yes,dogs
"""
    )
    return pd.read_csv(persons_attributes_csv)


@pytest.fixture
def extra_persons_attributes():
    persons_attributes_csv = StringIO(
        """
pid,hid,hzone,freq,income,age,driver,cats or dogs
0,0,Harrow,1,high,high,yes,dogs
1,0,Harrow,2,low,medium,no,dogs
2,1,Islington,1,medium,low,yes,dogs
3,1,Islington,1,medium,low,yes,dogs
"""
    )
    return pd.read_csv(persons_attributes_csv)


@pytest.fixture
def hhs_attributes():
    hhs_attributes_csv = StringIO(
        """
hid,hzone,freq,persons,cars
0,Harrow,1,2,1
1,Islington,2,1,1
"""
    )
    return pd.read_csv(hhs_attributes_csv)


test_trips_path = (pytest.test_data_dir / "simple_travel_diaries.csv").as_posix()
test_attributes_path = (pytest.test_data_dir / "simple_persons_data.csv").as_posix()
test_hhs_attributes_path = (pytest.test_data_dir / "simple_hhs_data.csv").as_posix()


# simple trips only cases


def test_build_population_trips_only(trips):
    population = build_population(trips=trips)
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 3,
    }


def test_build_population_trips_only_activity_encoding(activity_encoded_trips):
    population = build_population(trips=activity_encoded_trips)
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 3,
    }


def test_build_population_person_attributes_only(persons_attributes):
    population = build_population(persons_attributes=persons_attributes)
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 3,
    }


def test_build_population_person_attributes_only_with_extra_person(extra_persons_attributes):
    population = build_population(persons_attributes=extra_persons_attributes)
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 4,
    }


def test_build_population_hhs_only(hhs_attributes):
    population = build_population(hhs_attributes=hhs_attributes)
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 0,
    }


def test_build_population_from_persons_and_hhs(hhs_attributes, persons_attributes):
    population = build_population(
        persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    assert population.stats == {
        "num_activities": 0,
        "num_households": 2,
        "num_legs": 0,
        "num_people": 3,
    }


def test_read_trips_only(trips):
    population = load_travel_diary(trips=trips)
    assert len(population) == 3


def test_read_fail_with_no_trips_input():
    with pytest.raises(UserWarning):
        load_travel_diary(trips=None)


def test_trips_read_fail_with_no_pid_field(trips):
    trips_no_pid = trips.drop("pid", axis=1)
    with pytest.raises(UserWarning):
        load_travel_diary(trips=trips_no_pid)


def test_read_trips_from_path():
    population = load_travel_diary(trips=test_trips_path)
    assert len(population) == 23


def test_read_weights_from_trips(trips):
    population = load_travel_diary(trips=trips)
    assert population[1].freq == 6
    assert population[1][2].freq == 6


# trips and persons attributes cases


def test_read_trips_and_persons(trips, persons_attributes):
    population = load_travel_diary(trips=trips, persons_attributes=persons_attributes)
    assert len(population) == 3


def test_read_trips_and_persons_no_index(trips, persons_attributes):
    persons_attributes_ = persons_attributes.reset_index()
    population = load_travel_diary(trips=trips, persons_attributes=persons_attributes_)
    assert len(population) == 3


def test_read_fail_with_bad_trips_input():
    with pytest.raises(UserWarning):
        load_travel_diary(trips=None, persons_attributes=True)


def test_read_trips_and_persons_from_path():
    population = load_travel_diary(trips=test_trips_path, persons_attributes=test_attributes_path)
    assert len(population) == 23


def test_persons_read_fail_with_no_pid_field(trips, persons_attributes):
    persons_no_pid = persons_attributes.reset_index().drop("pid", axis=1)
    with pytest.raises(UserWarning):
        load_travel_diary(trips=trips, persons_attributes=persons_no_pid)


def test_persons_read_with_pid_not_as_index(trips, persons_attributes):
    persons_ = persons_attributes.reset_index()
    population = load_travel_diary(trips=trips, persons_attributes=persons_)
    assert len(population) == 3


def test_read_weights_from_persons(trips, persons_attributes):
    population = load_travel_diary(trips=trips, persons_attributes=persons_attributes)
    assert population[0].freq == 1.5
    assert population[0][0].freq == 1


def test_extra_person_stays_at_home(trips, extra_persons_attributes):
    population = load_travel_diary(trips=trips, persons_attributes=extra_persons_attributes)
    assert len(population[1][3].plan) == 1
    assert population[1][3].plan.day[0].act == "home"


# trips, persons and hhs attributes cases


def test_read_trips_and_persons_and_hhs(trips, persons_attributes, hhs_attributes):
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    assert len(population) == 3


def test_read_trips_and_persons_and_hhs_no_index(trips, persons_attributes, hhs_attributes):
    hhs_attributes.reset_index()
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    assert len(population) == 3


def test_read_trips_and_persons_and_hhs_from_paths():
    population = load_travel_diary(
        trips=test_trips_path,
        persons_attributes=test_attributes_path,
        hhs_attributes=test_hhs_attributes_path,
    )
    assert len(population) == 23


def test_read_fail_with_bad_hhs_input(trips, persons_attributes, hhs_attributes):
    with pytest.raises(UserWarning):
        load_travel_diary(trips=trips, persons_attributes=persons_attributes, hhs_attributes=True)


def test_read_hhs_with_missing_persons_input(trips, persons_attributes, hhs_attributes):
    population = load_travel_diary(
        trips=trips, persons_attributes=None, hhs_attributes=hhs_attributes
    )
    assert len(population) == 3


def test_read_hhs_with_missing_persons_input_and_no_trips_hid(
    trips, persons_attributes, hhs_attributes
):
    trips = trips.drop("hid", axis=1)
    population = load_travel_diary(
        trips=trips, persons_attributes=None, hhs_attributes=hhs_attributes
    )
    assert len(population) == 3
    for hid, hh in population:
        assert len(hh.people) == 1
        assert isinstance(hh[hid], Person)


def test_read_hh_weights_from_hhs(trips, persons_attributes, hhs_attributes):
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    assert population[0].freq == 1


# test ommitting sequence


def test_read_trips_with_seq(trips):
    population = load_travel_diary(trips=trips)
    population.validate()


def test_read_trips_without_seq(trips):
    trips_ = trips.drop("seq", axis=1)
    population = load_travel_diary(trips=trips_)
    population.validate()


def test_read_trips_without_seq_fail_if_out_of_order(trips):
    trips = trips.drop("seq", axis=1).iloc[::-1]
    population = load_travel_diary(trips=trips)
    with pytest.raises(PAMValidationLocationsError):
        population.validate()


# use trips input frequencies elsewhere


def test_use_trips_freq_as_persons_freq_overwrite(trips, persons_attributes):
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, trip_freq_as_person_freq=True
    )
    assert population[0][0].freq == 2


def test_use_trips_freq_as_persons_freq_no_persons_attributes(trips):
    population = load_travel_diary(
        trips=trips, persons_attributes=None, trip_freq_as_person_freq=True
    )
    assert population[0][0].freq == 2


def test_use_trips_freq_as_hhs_freq_overwrite(trips, persons_attributes, hhs_attributes):
    population = load_travel_diary(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes,
        trip_freq_as_hh_freq=True,
    )
    assert population[0].freq == 4


def test_use_trips_freq_as_hhs_freq_no_persons_attributes(trips):
    population = load_travel_diary(
        trips=trips, persons_attributes=None, hhs_attributes=None, trip_freq_as_hh_freq=True
    )
    assert population[0].freq == 4


def test_use_trips_freq_as_persons_and_hhs_freq_overwrite(
    trips, persons_attributes, hhs_attributes
):
    with pytest.raises(UserWarning):
        load_travel_diary(
            trips=trips,
            persons_attributes=persons_attributes,
            hhs_attributes=hhs_attributes,
            trip_freq_as_hh_freq=True,
            trip_freq_as_person_freq=True,
        )


def test_use_trips_freq_as_persons_and_hhs_freq_no_persons_attributes(trips):
    with pytest.raises(UserWarning):
        load_travel_diary(
            trips=trips,
            persons_attributes=None,
            hhs_attributes=None,
            trip_freq_as_hh_freq=True,
            trip_freq_as_person_freq=True,
        )


# test reading other trip encodings


def test_trip_based_encoding(trips):
    population = load_travel_diary(trips=trips, tour_based=False)
    assert len(population) == 3


def test_act_based_encoding(activity_encoded_trips):
    population = load_travel_diary(trips=activity_encoded_trips)
    assert len(population) == 3


# test inferring home location


def test_read_trips_location(trips):
    population = load_travel_diary(trips=trips, persons_attributes=None, hhs_attributes=None)
    assert population[0][0].home.area == "Harrow"

    # person and household location match
    for hid, pid, person in population.people():
        assert person.home.area == population[hid].location.area


def test_read_trips_and_persons_and_hhs_home_location(trips, persons_attributes, hhs_attributes):
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    assert population[0][0].home.area == "Harrow"

    # person and household location match
    for hid, pid, person in population.people():
        assert person.home.area == population[hid].location.area


def test_home_location_consistency_between_person_and_plan(
    trips, persons_attributes, hhs_attributes
):
    """Note that this works because people share a location object with their plans."""
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    hh = population[0]
    person = hh[0]
    assert person.home.area == "Harrow"
    assert person.plan.home == "Harrow"
    person.home.area = "Test"
    assert person.home.area == "Test"
    assert person.plan.home == "Test"


def test_home_location_consistency_between_hhs_and_persons_when_changing_hh_area(
    trips, persons_attributes, hhs_attributes
):
    population = load_travel_diary(
        trips=trips, persons_attributes=persons_attributes, hhs_attributes=hhs_attributes
    )
    hh = population[0]
    person = hh[0]

    assert hh.location.area == "Harrow"
    assert person.home == "Harrow"
    hh.location.area = "Test"
    assert person.home == "Harrow"  # no change
    hh.set_area("Test")
    hh.set_loc("Test")
    assert person.home == "Test"
    assert hh.location == person.home
