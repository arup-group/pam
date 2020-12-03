import pytest
from datetime import datetime, timedelta

from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.utils import timedelta_to_matsim_time as tdtm
from pam import PAMSequenceValidationError
from .fixtures import person_heh


def test_population_iadd_population():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household('2')
    p2 = Person('2')
    hh2.add(p2)
    pop2.add(hh2)

    pop1 += pop2
    assert set(pop1.households) == {'1', '2'}
    assert set(pop1.households['2'].people) == {'2'}
    assert isinstance(pop1.households['2'], Household)
    assert isinstance(pop1.households['2'].people['2'], Person)


def test_population_iadd_hh():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household('2')
    p2 = Person('2')
    hh2.add(p2)

    pop1 += hh2
    assert set(pop1.households) == {'1', '2'}
    assert set(pop1.households['2'].people) == {'2'}
    assert isinstance(pop1.households['2'], Household)
    assert isinstance(pop1.households['2'].people['2'], Person)


def test_population_iadd_person():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person('2')

    pop1 += p2
    assert set(pop1.households) == {'1', '2'}
    assert set(pop1.households['2'].people) == {'2'}
    assert isinstance(pop1.households['2'], Household)
    assert isinstance(pop1.households['2'].people['2'], Person)


def test_household_iadd_household():
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)

    hh2 = Household('2')
    p2 = Person('2')
    hh2.add(p2)

    hh1 += hh2
    assert set(hh1.people) == {'1', '2'}
    assert isinstance(hh1.people['2'], Person)


def test_household_iadd_person():
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)

    p2 = Person('2')

    hh1 += p2
    assert set(hh1.people) == {'1', '2'}
    assert isinstance(hh1.people['2'], Person)


def test_reindex_population():
    pop = Population()
    for i in ['1', '2']:
        hh = Household(i)
        pop.add(hh)
        for j in ['1', '2']:
            hh.add(Person(j))
    pop.reindex("test_")
    assert set(pop.households) == {'test_1', 'test_2'}
    assert {hh.hid for hh in pop.households.values()} == {'test_1', 'test_2'}
    assert set(pop.households['test_1'].people) == {'test_1', 'test_2'}
    assert {p.pid for p in pop.households['test_1'].people.values()} == {'test_1', 'test_2'}


def test_reindex_population_duplicate_key():
    pop = Population()
    for i in ['1', 'test_1']:
        hh = Household(i)
        pop.add(hh)
        for j in ['1', 'test_1']:
            hh.add(Person(j))
    with pytest.raises(KeyError):
        pop.reindex("test_")


def test_reindex_hh():
    hh = Household('1')
    for j in ['1', '2']:
        hh.add(Person(j))
    hh.reindex("test_")
    assert set(hh.people) == {'test_1', 'test_2'}


def test_reindex_hh_dupliate_key_error():
    hh = Household('1')
    for j in ['1', 'test_1']:
        hh.add(Person(j))
    with pytest.raises(KeyError):
        hh.reindex("test_")


def test_reindex_person():
    p = Person('1')
    p.reindex("test_")
    assert p.pid == 'test_1'


def test_population_combine_population():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household('1')
    p2 = Person('1')
    hh2.add(p2)
    pop2.add(hh2)

    pop1.combine(pop2, 'test_')
    assert set(pop1.households) == {'1', 'test_1'}
    assert set(pop1.households['test_1'].people) == {'test_1'}
    assert isinstance(pop1.households['test_1'], Household)
    assert isinstance(pop1.households['test_1'].people['test_1'], Person)


def test_population_combine_population_duplicate_key():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household('1')
    p2 = Person('1')
    hh2.add(p2)
    pop2.add(hh2)

    with pytest.raises(KeyError):
        pop1.combine(pop2, '')

