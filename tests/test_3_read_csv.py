import os
from io import StringIO
import pandas as pd
import pytest

from pam.read import load_travel_diary


trips_csv = StringIO("""
pid,hid,seq,hzone,ozone,dzone,purp,mode,tst,tet,freq
0,0,0,Harrow,Harrow,Camden,work,pt,444,473,1
0,0,1,Harrow,Camden,Harrow,home,pt,890,919,2
1,0,0,Harrow,Harrow,Tower Hamlets,work,car,507,528,3
1,0,1,Harrow,Tower Hamlets,Harrow,home,car,1065,1086,4
2,1,0,Islington,Islington,Hackney,shop,pt,422,425,5
2,1,1,Islington,Hackney,Hackney,leisure,walk,485,500,6
2,1,2,Islington,Croydon,Islington,home,pt,560,580,7
""")

persons_attributes_csv = StringIO("""
pid,hid,hzone,freq,income,age,driver,cats or dogs
0,0,Harrow,1,high,high,yes,dogs
1,0,Harrow,2,low,medium,no,dogs
2,1,Islington,1,medium,low,yes,dogs
""")

hhs_attributes_csv = StringIO("""
hid,hzone,freq,persons,cars
0,Harrow,1,2,1
1,Islington,2,1,1
""")

trips = pd.read_csv(trips_csv)
persons_attributes = pd.read_csv(persons_attributes_csv)
hhs_attributes = pd.read_csv(hhs_attributes_csv)

test_trips_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_travel_diaries.csv")
)

test_attributes_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data/simple_persons_data.csv")
)


def test_read_trips_only():
    population = load_travel_diary(trips=trips)
    assert len(population) == 3


def test_read_fail_with_no_trips_input():
    with pytest.raises(UserWarning):
        population = load_travel_diary(trips=None)


def test_trips_read_fail_with_no_pid_field():
    trips_no_pid = trips.drop('pid', axis=1)
    with pytest.raises(UserWarning):
        population = load_travel_diary(trips=trips_no_pid)


def test_read_trips_from_path():
    population = load_travel_diary(trips=test_trips_path)
    assert len(population) == 23


def test_read_weights_from_trips():
    population = load_travel_diary(trips=trips)
    assert population['1'].freq == 6
    assert population['1']['2'].freq == 6


def test_read_trips_and_persons():
    population = load_travel_diary(trips=trips, persons_attributes=persons_attributes)
    assert len(population) == 3


def test_read_fail_with_bad_trips_input():
    with pytest.raises(UserWarning):
        population = load_travel_diary(trips=None, persons_attributes=True)


def test_read_trips_and_persons_from_path():
    population = load_travel_diary(trips=test_trips_path, persons_attributes=test_attributes_path)
    assert len(population) == 23


def test_persons_read_fail_with_no_pid_field():
    persons_no_pid = persons_attributes.reset_index().drop('pid', axis=1)
    with pytest.raises(UserWarning):
        population = load_travel_diary(trips=trips, persons_attributes=persons_no_pid)


def test_persons_read_with_pid_not_as_index():
    persons_ = persons_attributes.reset_index()
    population = load_travel_diary(trips=trips, persons_attributes=persons_)
    assert len(population) == 3


def test_read_weights_from_persons():
    print(persons_attributes.columns)
    print(persons_attributes.index.name)
    population = load_travel_diary(trips=trips, persons_attributes=persons_attributes)
    assert population['0'].freq == 1.5
    assert population['0']['0'].freq == 1


def test_read_trips_and_persons_and_hhs():
    population = load_travel_diary(
        trips=trips,
        persons_attributes=persons_attributes,
        hhs_attributes=hhs_attributes
        )
    assert len(population) == 3


def test_read_fail_with_bad_hhs_input():
    with pytest.raises(UserWarning):
        population = load_travel_diary(
            trips=trips,
            persons_attributes=persons_attributes,
            hhs_attributes=True
            )


def test_read_fail_with_missing_persons_input():
    population = load_travel_diary(
        trips=trips,
        persons_attributes=None,
        hhs_attributes=hhs_attributes
        )
    assert len(population) == 3