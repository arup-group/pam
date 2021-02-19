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


def test_population_combine_household():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household('1')
    p2 = Person('1')
    hh2.add(p2)

    pop1.combine(hh2, 'test_')
    assert set(pop1.households) == {'1', 'test_1'}
    assert set(pop1.households['test_1'].people) == {'test_1'}
    assert isinstance(pop1.households['test_1'], Household)
    assert isinstance(pop1.households['test_1'].people['test_1'], Person)


def test_population_combine_person():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person('1')

    pop1.combine(p2, 'test_')
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


def test_population_combine_household_duplicate_key():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household('1')
    p2 = Person('1')
    hh2.add(p2)

    with pytest.raises(KeyError):
        pop1.combine(hh2, '')


def test_population_combine_person_duplicate_key():
    pop1 = Population()
    hh1 = Household('1')
    p1 = Person('1')
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person('1')

    with pytest.raises(KeyError):
        pop1.combine(p2, '')


def test_population_contains_hh():
    population = Population()
    hh = Household('A', attributes={1:1})
    p = Person('person_A', attributes={1:1})
    hh.add(p)
    population.add(hh)

    # same hh and person
    hh2 = Household('A', attributes={1:1})
    p2 = Person('person_A', attributes={1:1})
    hh2.add(p2)
    assert hh2 in population

    # same hh and person diff index for hh
    hh2 = Household('X', attributes={1:1})
    p2 = Person('person_A', attributes={1:1})
    hh2.add(p2)
    assert hh2 in population

    # same hh and person diff indexes
    # hh2 = Household('X', attributes={1:1})
    # p2 = Person('person_X', attributes={1:1})
    # hh2.add(p2)
    # assert hh2 in population

    # diff person and diff hh
    hh3 = Household('B', attributes={1:2})
    p3 = Person('person_B', attributes={1:3})
    hh3.add(p3)
    assert hh3 not in population

    # diff hh and same person
    hh4 = Household('B', attributes={1:2})
    p4 = Person('person_A', attributes={1:1})
    hh4.add(p4)
    assert hh4 not in population

    # same hh and diff person
    hh5 = Household('A', attributes={1:1})
    p5 = Person('person_A', attributes={1:4})
    hh4.add(p5)
    assert hh5 not in population


def test_population_contains_person():
    population = Population()
    hh = Household('A', attributes={1:1})
    p = Person('person_A', attributes={1:1})
    hh.add(p)
    population.add(hh)

    # same person
    p2 = Person('person_A', attributes={1:1})
    assert p2 in population

    # diff person index
    p2 = Person('person_X', attributes={1:1})
    assert p2 in population

    # diff person
    p2 = Person('person_A', attributes={1:2})
    assert p2 not in population


def test_population_contains_wrong_type():
    population = Population()
    with pytest.raises(UserWarning):
        assert None in population


def test_hh_contains_person():
    hh = Household('A', attributes={1:1})
    p = Person('person_A', attributes={1:1})
    hh.add(p)

    # same person
    p2 = Person('person_A', attributes={1:1})
    assert p2 in hh

    # diff person index
    p2 = Person('person_X', attributes={1:1})
    assert p2 in hh

    # diff person
    p2 = Person('person_A', attributes={1:2})
    assert p2 not in hh


def test_hh_contains_wrong_type():
    hh = Household(1)
    with pytest.raises(UserWarning):
        assert None in hh

def test_persons_equal_with_attributes():
    p1 = Person(1, attributes = {1:1})
    p2 = Person(1, attributes = {1:1})
    p3 = Person(2, attributes = {1:1})
    p4 = Person(1, attributes = {1:2})
    assert p1 == p2
    assert p1 == p1
    assert p2 == p3
    assert not p1 == p4
    assert not p1 == None


def test_persons_equal_with_plans():
    p1 = Person('1', attributes = {1:1})
    p1.plan.day = [
        Activity(act='a', area=1, start_time=0, end_time=1),
        Leg(mode='car', start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act='b', area=2, start_time=2, end_time=4)
    ]
    p2 = Person('2', attributes = {1:1})
    p2.plan.day = [
        Activity(act='a', area=1, start_time=0, end_time=1),
        Leg(mode='car', start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act='b', area=2, start_time=2, end_time=4)
    ]
    p3 = Person('3', attributes = {1:2})
    p3.plan.day = [
        Activity(act='a', area=1, start_time=0, end_time=1),
        Leg(mode='car', start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act='b', area=2, start_time=2, end_time=4)
    ]
    p4 = Person('4', attributes = {1:1})
    p4.plan.day = [
        Activity(act='a', area=1, start_time=0, end_time=1),
        Leg(mode='car', start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act='b', area=3, start_time=2, end_time=4)
    ]
    assert p1 == p1
    assert p1 == p2
    assert not p1 == p3
    assert not p1 == p4
    assert not p1 == None


def test_hhs_equal_with_attributes():
    hh1 = Household('1', attributes = {1:1})
    hh2 = Household('1', attributes = {1:1})
    hh3 = Household('2', attributes = {1:1})
    hh4 = Household('1', attributes = {1:2})
    assert hh1 == hh2
    assert hh1 == hh1
    assert hh2 == hh3
    assert not hh1 == hh4
    assert not hh1 == None


def test_hhs_equal_with_persons():
    hh1 = Household('1', attributes={1:1})
    p1 = Person('1', attributes={1:1})
    hh1.add(p1)

    hh2 = Household('1', attributes={1:1})
    p2 = Person('1', attributes={1:1})
    hh2.add(p2)

    hh3 = Household('2', attributes={1:1})
    p3 = Person('2', attributes={1:1})
    hh3.add(p3)

    hh4 = Household('2', attributes={1:2})

    hh5 = Household('2', attributes={1:1})
    p5 = Person('1', attributes={1:2})
    hh5.add(p5)

    assert hh1 == hh1
    assert hh1 == hh2
    assert not hh1 == hh3
    assert not hh1 == hh4
    assert not hh1 == hh5


def test_populations_equal():
    pop1 = Population()
    hh1 = Household('1', attributes={1:1})
    p1 = Person('1', attributes={1:1})
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household('1', attributes={1:1})
    p2 = Person('1', attributes={1:1})
    hh2.add(p2)
    pop2.add(hh2)

    pop3 = Population()
    hh3 = Household('2', attributes={1:1})
    p3 = Person('2', attributes={1:1})
    hh3.add(p3)
    pop3.add(hh3)

    pop4 = Population()
    hh4 = Household('2', attributes={1:2})
    pop4.add(hh4)

    pop5 = Population()
    hh5 = Household('2', attributes={1:1})
    p5 = Person('1', attributes={1:2})
    hh5.add(p5)
    pop5.add(hh5)

    assert pop1 == pop1
    assert pop1 == pop2
    assert not pop1 == pop3
    assert not pop1 == pop4
    assert not pop1 == pop5
