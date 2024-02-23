import pytest
from pam.activity import Activity, Leg
from pam.core import Household, Person, Population


def test_get_last_component_activity():
    p = Person(0)
    p.add(Activity())
    assert isinstance(p.last_component, Activity)


def test_get_last_component_leg():
    p = Person(0)
    p.add(Activity())
    p.add(Leg())
    assert isinstance(p.last_component, Leg)


def test_get_last_activity():
    p = Person(0)
    p.add(Activity())
    p.add(Leg())
    p.add(Activity(seq=2))
    p.add(Leg())
    assert isinstance(p.last_activity, Activity)
    assert p.last_activity.seq == 2


def test_get_last_component_empty():
    p = Person(0)
    assert p.last_component is None


def test_get_last_leg():
    p = Person(0)
    p.add(Activity())
    p.add(Leg())
    p.add(Activity())
    p.add(Leg(seq=2))
    p.add(Activity())
    assert isinstance(p.last_leg, Leg)
    assert p.last_leg.seq == 2


def test_get_last_leg_empty():
    p = Person(0)
    assert p.last_leg is None


def test_population_add():
    pop = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop.add(hh1)
    assert "1" in pop.households

    hh2 = Household("2")
    p2 = Person("2")
    hh2.add(p2)
    hh3 = Household("3")
    p3 = Person("3")
    hh3.add(p3)

    pop.add([hh2, hh3])
    assert set(pop.households) == {"1", "2", "3"}


def test_population_iadd_population():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household("2")
    p2 = Person("2")
    hh2.add(p2)
    pop2.add(hh2)

    pop1 += pop2
    assert set(pop1.households) == {"1", "2"}
    assert set(pop1.households["2"].people) == {"2"}
    assert isinstance(pop1.households["2"], Household)
    assert isinstance(pop1.households["2"].people["2"], Person)


def test_population_iadd_hh():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household("2")
    p2 = Person("2")
    hh2.add(p2)

    pop1 += hh2
    assert set(pop1.households) == {"1", "2"}
    assert set(pop1.households["2"].people) == {"2"}
    assert isinstance(pop1.households["2"], Household)
    assert isinstance(pop1.households["2"].people["2"], Person)


def test_population_iadd_person():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person("2")

    pop1 += p2
    assert set(pop1.households) == {"1", "2"}
    assert set(pop1.households["2"].people) == {"2"}
    assert isinstance(pop1.households["2"], Household)
    assert isinstance(pop1.households["2"].people["2"], Person)


def test_household_iadd_household():
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)

    hh2 = Household("2")
    p2 = Person("2")
    hh2.add(p2)

    hh1 += hh2
    assert set(hh1.people) == {"1", "2"}
    assert isinstance(hh1.people["2"], Person)


def test_household_iadd_person():
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)

    p2 = Person("2")

    hh1 += p2
    assert set(hh1.people) == {"1", "2"}
    assert isinstance(hh1.people["2"], Person)


def test_reindex_population():
    pop = Population()
    for i in ["1", "2"]:
        hh = Household(i)
        pop.add(hh)
        for j in ["1", "2"]:
            hh.add(Person(j))
    pop.reindex("test_")
    assert set(pop.households) == {"test_1", "test_2"}
    assert {hh.hid for hh in pop.households.values()} == {"test_1", "test_2"}
    assert set(pop.households["test_1"].people) == {"test_1", "test_2"}
    assert {p.pid for p in pop.households["test_1"].people.values()} == {"test_1", "test_2"}


def test_reindex_population_duplicate_key():
    pop = Population()
    for i in ["1", "test_1"]:
        hh = Household(i)
        pop.add(hh)
        for j in ["1", "test_1"]:
            hh.add(Person(j))
    with pytest.raises(KeyError):
        pop.reindex("test_")


def test_reindex_hh():
    hh = Household("1")
    for j in ["1", "2"]:
        hh.add(Person(j))
    hh.reindex("test_")
    assert set(hh.people) == {"test_1", "test_2"}


def test_reindex_hh_dupliate_key_error():
    hh = Household("1")
    for j in ["1", "test_1"]:
        hh.add(Person(j))
    with pytest.raises(KeyError):
        hh.reindex("test_")


def test_reindex_person():
    p = Person("1")
    p.reindex("test_")
    assert p.pid == "test_1"


def test_population_combine_population():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household("1")
    p2 = Person("1")
    hh2.add(p2)
    pop2.add(hh2)

    pop1.combine(pop2, "test_")
    assert set(pop1.households) == {"1", "test_1"}
    assert set(pop1.households["test_1"].people) == {"test_1"}
    assert isinstance(pop1.households["test_1"], Household)
    assert isinstance(pop1.households["test_1"].people["test_1"], Person)


def test_population_combine_household():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household("1")
    p2 = Person("1")
    hh2.add(p2)

    pop1.combine(hh2, "test_")
    assert set(pop1.households) == {"1", "test_1"}
    assert set(pop1.households["test_1"].people) == {"test_1"}
    assert isinstance(pop1.households["test_1"], Household)
    assert isinstance(pop1.households["test_1"].people["test_1"], Person)


def test_population_combine_person():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person("1")

    pop1.combine(p2, "test_")
    assert set(pop1.households) == {"1", "test_1"}
    assert set(pop1.households["test_1"].people) == {"test_1"}
    assert isinstance(pop1.households["test_1"], Household)
    assert isinstance(pop1.households["test_1"].people["test_1"], Person)


def test_population_combine_population_duplicate_key():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household("1")
    p2 = Person("1")
    hh2.add(p2)
    pop2.add(hh2)

    with pytest.raises(KeyError):
        pop1.combine(pop2, "")


def test_population_combine_household_duplicate_key():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    hh2 = Household("1")
    p2 = Person("1")
    hh2.add(p2)

    with pytest.raises(KeyError):
        pop1.combine(hh2, "")


def test_population_combine_person_duplicate_key():
    pop1 = Population()
    hh1 = Household("1")
    p1 = Person("1")
    hh1.add(p1)
    pop1.add(hh1)

    p2 = Person("1")

    with pytest.raises(KeyError):
        pop1.combine(p2, "")


@pytest.fixture()
def population():
    population = Population()
    hh = Household("A", attributes={1: 1})
    pa = Person("person_A", attributes={1: 1})
    hh.add(pa)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    population.add(hh)
    population.add(Household("B"))
    return population


def test_population_contains_hh_with_same_hh_and_person(population):
    hh = Household("A", attributes={1: 1})
    p2 = Person("person_A", attributes={1: 1})
    hh.add(p2)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh in population


def test_population_contains_hh_with_same_hh_and_person_diff_index_for_hh(population):
    hh = Household("X", attributes={1: 1})
    p2 = Person("person_A", attributes={1: 1})
    hh.add(p2)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh in population


def test_population_contains_hh_with_same_hh_and_person_diff_indexes(population):
    hh = Household("X", attributes={1: 1})
    p2 = Person("person_X", attributes={1: 1})
    hh.add(p2)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh in population


def test_population_not_contains_hh_with_diff_person_and_diff_hh(population):
    hh = Household("B", attributes={1: 2})
    p3 = Person("person_B", attributes={1: 3})
    hh.add(p3)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh not in population


def test_population_not_contains_hh_with_diff_hh_and_same_person(population):
    hh = Household("B", attributes={1: 2})
    p4 = Person("person_A", attributes={1: 1})
    hh.add(p4)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh not in population


def test_population_not_contains_hh_same_hh_and_diff_person(population):
    hh = Household("A", attributes={1: 1})
    p5 = Person("person_A", attributes={1: 4})
    hh.add(p5)
    pb = Person("Person_B", attributes={1: 3})
    hh.add(pb)
    assert hh not in population


def test_population_not_contains_hh_same_hh_and_diff_num_persons(population):
    hh = Household("A", attributes={1: 1})
    p5 = Person("person_A", attributes={1: 1})
    hh.add(p5)
    assert hh not in population


def test_population_contains_person_same_person(population):
    p2 = Person("person_A", attributes={1: 1})
    assert p2 in population


def test_population_contains_person_with_diff_index(population):
    p2 = Person("person_X", attributes={1: 1})
    assert p2 in population


def test_population_not_contains_diff_person(population):
    p2 = Person("person_A", attributes={1: 2})
    assert p2 not in population


def test_population_contains_wrong_type():
    population = Population()
    with pytest.raises(UserWarning):
        assert None in population


@pytest.fixture()
def hh():
    hh = Household("A", attributes={1: 1})
    p = Person("person_A", attributes={1: 1})
    hh.add(p)
    return hh


def test_hh_contains_same_person(hh):
    p2 = Person("person_A", attributes={1: 1})
    assert p2 in hh


def test_hh_contains_person_with_diff_index(hh):
    p2 = Person("person_X", attributes={1: 1})
    assert p2 in hh


def test_hh_not_contains_diff_person(hh):
    p2 = Person("person_A", attributes={1: 2})
    assert p2 not in hh


def test_hh_contains_wrong_type():
    hh = Household(1)
    with pytest.raises(UserWarning):
        assert None in hh


def test_same_persons_equal():
    p1 = Person(1, attributes={1: 1})
    assert p1 == p1


def test_persons_equal_with_same_attributes():
    p1 = Person(1, attributes={1: 1})
    p2 = Person(1, attributes={1: 1})
    assert p1 == p2


def test_persons_equal_with_same_attributes_diff_index():
    p1 = Person(1, attributes={1: 1})
    p3 = Person(2, attributes={1: 1})
    assert p1 == p3


def test_persons_not_equal_with_diff_attributes():
    p1 = Person(1, attributes={1: 1})
    p4 = Person(1, attributes={1: 2})
    assert not p1 == p4


def test_persons_not_equal_with_wrong_type():
    p1 = Person(1, attributes={1: 1})
    assert p1 is not None


def test_persons_equal_with_plans_same_person():
    p1 = Person("1", attributes={1: 1})
    p1.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    assert p1 == p1


def test_persons_equal_with_same_plans():
    p1 = Person("1", attributes={1: 1})
    p1.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    p2 = Person("2", attributes={1: 1})
    p2.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    assert p1 == p2


def test_persons_not_equal_with_plans_diff_attributes_same_plan():
    p1 = Person("1", attributes={1: 1})
    p1.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    p3 = Person("3", attributes={1: 2})
    p3.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    assert not p1 == p3


def test_persons_not_equal_with_diff_plans():
    p1 = Person("1", attributes={1: 1})
    p1.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=2, start_time=2, end_time=4),
    ]
    p4 = Person("4", attributes={1: 1})
    p4.plan.day = [
        Activity(act="a", area=1, start_time=0, end_time=1),
        Leg(mode="car", start_area=1, end_area=2, start_time=1, end_time=2),
        Activity(act="b", area=3, start_time=2, end_time=4),
    ]
    assert not p1 == p4


def test_hhs_equal_with_attributes_same_hh():
    hh1 = Household("1", attributes={1: 1})
    assert hh1 == hh1


def test_hhs_equal_with_same_attributes():
    hh1 = Household("1", attributes={1: 1})
    hh2 = Household("1", attributes={1: 1})
    assert hh1 == hh2


def test_hhs_equal_with_same_attributes_diff_index():
    hh1 = Household("1", attributes={1: 1})
    hh3 = Household("2", attributes={1: 1})
    assert hh1 == hh3


def test_hhs_not_equal_with_diff_attributes():
    hh1 = Household("1", attributes={1: 1})
    hh4 = Household("1", attributes={1: 2})
    assert not hh1 == hh4


def test_hhs_not_equal_with_diff_type():
    hh1 = Household("1", attributes={1: 1})
    assert hh1 is not None


def test_hhs_equal_with_persons():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    hh2 = Household("1", attributes={1: 1})
    p2 = Person("1", attributes={1: 1})
    hh2.add(p2)

    hh3 = Household("2", attributes={1: 1})
    p3 = Person("2", attributes={1: 1})
    hh3.add(p3)

    hh4 = Household("2", attributes={1: 2})

    hh5 = Household("2", attributes={1: 1})
    p5 = Person("1", attributes={1: 2})
    hh5.add(p5)

    assert hh1 == hh1
    assert hh1 == hh2
    assert hh1 == hh3
    assert not hh1 == hh4
    assert not hh1 == hh5


def test_hhs_equal_with_persons_same_hh():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    assert hh1 == hh1


def test_hhs_with_persons_equal_with_same_persons():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    hh2 = Household("1", attributes={1: 1})
    p2 = Person("1", attributes={1: 1})
    hh2.add(p2)

    assert hh1 == hh2


def test_hhs_with_persons_equal_with_same_persons_diff_pid():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    hh3 = Household("2", attributes={1: 1})
    p3 = Person("2", attributes={1: 1})
    hh3.add(p3)

    assert hh1 == hh3


def test_hhs_not_equal_with_missing_persons():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    hh4 = Household("2", attributes={1: 2})

    assert not hh1 == hh4


def test_hhs_not_equal_with_diff_persons_attributes():
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)

    hh5 = Household("2", attributes={1: 1})
    p5 = Person("1", attributes={1: 2})
    hh5.add(p5)

    assert not hh1 == hh5


def test_population_equals_wrong_types():
    pop1 = Population()
    with pytest.raises(UserWarning):
        pop1 == 3


def test_populations_equal_given_same_population():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    assert pop1 == pop1


def test_populations_equal_with_same_hh_and_person_attributes():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    pop2 = Population()
    hh2 = Household("1", attributes={1: 1})
    p2 = Person("1", attributes={1: 1})
    hh2.add(p2)
    pop2.add(hh2)

    assert pop1 == pop2


def test_populations_equal_given_same_hh_and_persons_with_diff_ids():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    pop3 = Population()
    hh3 = Household("2", attributes={1: 1})
    p3 = Person("2", attributes={1: 1})
    hh3.add(p3)
    pop3.add(hh3)

    assert pop1 == pop3


def test_populations_not_equal_given_missing_person():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    pop4 = Population()
    hh4 = Household("2", attributes={1: 2})
    pop4.add(hh4)

    assert not pop1 == pop4


def test_populations_not_equal_given_wrong_person_attributes():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    pop5 = Population()
    hh5 = Household("2", attributes={1: 1})
    p5 = Person("1", attributes={1: 2})
    hh5.add(p5)
    pop5.add(hh5)

    assert not pop1 == pop5


def test_populations_not_equal_given_diff_type():
    pop1 = Population()
    hh1 = Household("1", attributes={1: 1})
    p1 = Person("1", attributes={1: 1})
    hh1.add(p1)
    pop1.add(hh1)

    assert pop1 is not None
