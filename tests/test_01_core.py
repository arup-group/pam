from datetime import datetime, timedelta

import pytest
from pam import PAMSequenceValidationError, PAMTimesValidationError, PAMValidationLocationsError
from pam.activity import Activity, Leg
from pam.core import Household, Person, Population
from pam.utils import minutes_to_datetime as mtdt
from pam.utils import timedelta_to_matsim_time as tdtm
from pam.variables import END_OF_DAY

testdata = [
    (0, datetime(1900, 1, 1, 0, 0)),
    (30, datetime(1900, 1, 1, 0, 30)),
    (300, datetime(1900, 1, 1, 5, 0)),
    (330, datetime(1900, 1, 1, 5, 30)),
]


@pytest.mark.parametrize("m,expected", testdata)
def test_minutes_to_dt(m, expected):
    assert mtdt(m) == expected


testdata = [
    (timedelta(seconds=0), "00:00:00"),
    (timedelta(hours=1), "01:00:00"),
    (timedelta(hours=11, minutes=1, seconds=3), "11:01:03"),
]


@pytest.mark.parametrize("td,expected", testdata)
def test_td_to_matsim_string(td, expected):
    assert tdtm(td) == expected


def test_population_add_household():
    population = Population()
    household = Household("1")
    population.add(household)
    assert len(population.households) == 1
    assert list(population.households) == ["1"]


def test_population_add_household_error():
    population = Population()
    household = None
    with pytest.raises(UserWarning):
        population.add(household)


def test_household_add_person():
    household = Household("1")
    person = Person("1")
    person.add(Activity(1, "home", 1, start_time=0))
    household.add(person)
    assert len(household.people) == 1
    assert list(household.people) == ["1"]


def test_household_add_person_error():
    household = Household("1")
    person = None
    with pytest.raises(UserWarning):
        household.add(person)


def test_person_add_activity():
    person = Person("1")
    act = Activity(1, "home", 1)
    person.add(act)
    assert len(person.plan) == 1


def test_person_add_leg():
    person = Person("1")
    act = Activity(1, "home", 1)
    person.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2)
    person.add(leg)
    assert len(person.plan) == 2


def test_person_add_activity_activity_raise_error():
    person = Person("1")
    act = Activity(1, "home", 1)
    person.add(act)
    act = Activity(2, "work", 1)
    with pytest.raises(PAMSequenceValidationError):
        person.add(act)


def test_person_add_leg_first_raise_error():
    person = Person("1")
    leg = Leg(1, "car", start_area=1, end_area=2)
    with pytest.raises(PAMSequenceValidationError):
        person.add(leg)


def test_person_add_leg_leg_raise_error():
    person = Person("1")
    act = Activity(1, "home", 1)
    person.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2)
    person.add(leg)
    leg = Leg(2, "car", start_area=2, end_area=1)
    with pytest.raises(PAMSequenceValidationError):
        person.add(leg)


def test_yield_plan():
    person = Person("1")
    act = Activity(1, "home", 1)
    person.add(act)
    leg = Leg(1, "car", start_area=1, end_area=2)
    person.add(leg)
    yield_plan = [c for c in person]
    assert len(yield_plan) == 2
    assert isinstance(yield_plan[0], Activity)
    assert isinstance(yield_plan[1], Leg)


def test_person_validate_sequence():
    person = Person("1")
    person.plan.day = [
        Activity(act="home", area=1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(start_area=1, end_area=2, start_time=mtdt(1), end_time=mtdt(2)),
        Activity(act="work", area=2, start_time=mtdt(2), end_time=END_OF_DAY),
    ]
    assert person.validate_sequence()


def test_person_validate_sequence_fail1():
    person = Person("1")
    person.plan.day = [Activity(1, "home", 1), Leg(1, "car", start_area=1, end_area=2)]
    with pytest.raises(PAMSequenceValidationError):
        assert person.validate_sequence()


def test_person_validate_sequence_fail2():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1),
        Leg(1, "car", start_area=1, end_area=2),
        Leg(1, "car", start_area=1, end_area=2),
        Activity(),
    ]
    with pytest.raises(PAMSequenceValidationError):
        assert person.validate_sequence()


def test_person_validate_times():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(1), end_time=mtdt(2)),
        Activity(1, "work", 2, start_time=mtdt(2), end_time=END_OF_DAY),
    ]
    assert person.validate_times()


def test_person_validate_times_fail():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(0), end_time=mtdt(1)),
        Activity(1, "work", 2, start_time=mtdt(2), end_time=END_OF_DAY),
    ]
    with pytest.raises(PAMTimesValidationError):
        assert person.validate_times()


def test_person_validate_times_gap_fail():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(10), end_time=mtdt(11)),
        Activity(1, "work", 2, start_time=mtdt(11), end_time=END_OF_DAY),
    ]
    person.validate_sequence()
    with pytest.raises(PAMTimesValidationError):
        assert person.validate_times()


def test_person_validate_locations():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", start_time=mtdt(0), end_time=mtdt(1), area=1),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(1), end_time=mtdt(2)),
        Activity(1, "work", 2, start_time=mtdt(2), end_time=END_OF_DAY),
    ]
    assert person.validate_locations()


def test_person_validate_locations_fail():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", start_time=mtdt(0), end_time=mtdt(1), area=2),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(0), end_time=mtdt(1)),
        Activity(1, "work", 1, start_time=mtdt(1), end_time=END_OF_DAY),
    ]
    with pytest.raises(PAMValidationLocationsError):
        assert person.validate_locations()


def test_crop_plan():
    person = Person("1")
    person.plan.day = [Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(25 * 60))]
    person.fix_plan()
    assert person.validate_sequence()


def test_fix_time_consistency_plan():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(1, "car", start_area=1, end_area=2, start_time=mtdt(10), end_time=mtdt(11)),
    ]
    person.fix_plan()
    assert person.validate_sequence()


def test_fix_location_consistency_plan():
    person = Person("1")
    person.plan.day = [
        Activity(1, "home", 1, start_time=mtdt(0), end_time=mtdt(1)),
        Leg(1, "car", start_area=2, end_area=2, start_time=mtdt(1), end_time=mtdt(2)),
    ]
    person.fix_plan()
    assert person.validate_sequence()


def test_person_home_based():
    person = Person("1")
    person.add(Activity(1, "home", 1))
    person.add(Leg(1, "car", start_area=1, end_area=2))
    person.add(Activity(2, "work", 1))
    person.add(Leg(2, "car", start_area=2, end_area=1))
    person.add(Activity(3, "home", 1))
    assert person.home_based


def test_person_not_home_based():
    person = Person("1")
    person.add(Activity(1, "work", 1))
    person.add(Leg(1, "car", start_area=1, end_area=2))
    person.add(Activity(2, "home", 1))
    person.add(Leg(2, "car", start_area=2, end_area=1))
    person.add(Activity(3, "work", 1))
    assert not person.home_based


def test_person_closed_plan():
    person = Person("1")
    person.add(Activity(1, "home", 1))
    person.add(Leg(1, "car", start_area=1, end_area=2))
    person.add(Activity(2, "work", 1))
    person.add(Leg(2, "car", start_area=2, end_area=1))
    person.add(Activity(3, "home", 1))
    assert person.closed_plan


def test_person_not_closed_plan_different_acts():
    person = Person("1")
    person.add(Activity(1, "work", 1))
    person.add(Leg(1, "car", start_area=1, end_area=2))
    person.add(Activity(2, "home", 1))
    assert not person.closed_plan


def test_person_not_closed_plan_different_areas():
    person = Person("1")
    person.add(Activity(1, "work", 1))
    person.add(Leg(1, "car", start_area=1, end_area=2))
    person.add(Activity(2, "home", 1))
    person.add(Leg(2, "car", start_area=2, end_area=3))
    person.add(Activity(3, "work", 3))
    assert not person.closed_plan


def test_extract_person_activity_classes():
    person = Person(pid=str(1))
    person.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    person.add(
        Leg(
            seq=2,
            mode="bike",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    person.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    person.add(
        Leg(
            seq=2,
            mode="pt",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
        )
    )
    person.add(Activity(seq=3, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))

    assert person.activity_classes == set(["home", "work"])


def test_extract_person_mode_classes():
    person = Person(pid=str(1))
    person.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    person.add(
        Leg(
            seq=2,
            mode="bike",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    person.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    person.add(
        Leg(
            seq=2,
            mode="pt",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(1220),
        )
    )
    person.add(Activity(seq=3, act="home", area="A", start_time=mtdt(1220), end_time=mtdt(1500)))

    assert person.mode_classes == set(["bike", "pt"])


def test_extract_household_activity_classes():
    household = Household(hid="1")
    for i, (act, mode) in enumerate(zip(["work", "school"], ["car", "pt"])):
        person = Person(pid=str(i))
        person.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
        person.add(
            Leg(
                seq=2,
                mode=mode,
                start_area="A",
                end_area="B",
                start_time=mtdt(600),
                end_time=mtdt(620),
            )
        )
        person.add(Activity(seq=3, act=act, area="B", start_time=mtdt(620), end_time=mtdt(1200)))
        household.add(person)

    assert household.activity_classes == set(["home", "work", "school"])


def test_extract_household_mode_classes():
    household = Household(hid="1")
    for i, (act, mode) in enumerate(zip(["work", "school"], ["car", "pt"])):
        person = Person(pid=str(i))
        person.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
        person.add(
            Leg(
                seq=2,
                mode=mode,
                start_area="A",
                end_area="B",
                start_time=mtdt(600),
                end_time=mtdt(620),
            )
        )
        person.add(Activity(seq=3, act=act, area="B", start_time=mtdt(620), end_time=mtdt(1200)))
        household.add(person)

    assert household.mode_classes == set(["car", "pt"])


def test_extract_population_activity_classes():
    population = Population()
    for hid, (_act, _mode) in enumerate(zip(["leisure", "shop"], ["car", "walk"])):
        household = Household(hid=str(hid))
        population.add(household)
        for i, (act, mode) in enumerate(zip(["work", _act], ["car", _mode])):
            person = Person(pid=str(i))
            person.add(
                Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600))
            )
            person.add(
                Leg(
                    seq=2,
                    mode=mode,
                    start_area="A",
                    end_area="B",
                    start_time=mtdt(600),
                    end_time=mtdt(620),
                )
            )
            person.add(
                Activity(seq=3, act=act, area="B", start_time=mtdt(620), end_time=mtdt(1200))
            )
            household.add(person)

    assert population.activity_classes == set(["home", "leisure", "work", "shop"])


def test_extract_population_mode_classes():
    population = Population()
    for hid, (_act, _mode) in enumerate(zip(["work", "shop"], ["pt", "walk"])):
        household = Household(hid=str(hid))
        population.add(household)
        for i, (act, mode) in enumerate(zip(["work", _act], ["car", _mode])):
            person = Person(pid=str(i))
            person.add(
                Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600))
            )
            person.add(
                Leg(
                    seq=2,
                    mode=mode,
                    start_area="A",
                    end_area="B",
                    start_time=mtdt(600),
                    end_time=mtdt(620),
                )
            )
            person.add(
                Activity(seq=3, act=act, area="B", start_time=mtdt(620), end_time=mtdt(1200))
            )
            household.add(person)

    assert population.mode_classes == set(["car", "pt", "walk"])


def test_count_population():
    population = Population()
    for i in range(1, 5):
        hh = Household(str(i))
        for ii in range(i):
            hh.add(Person(f"{i}_{ii}"))
        population.add(hh)
    assert population.population == 10


def test_population_get_random_household():
    population = Population()
    population.add(Household("1"))
    population.add(Household("2"))
    assert isinstance(population.random_household(), Household)


def test_population_get_random_person():
    population = Population()
    population.add(Household("1"))
    population["1"].add(Person("0"))
    population["1"].add(Person("1"))
    assert isinstance(population.random_person(), Person)


def test_population_size():
    population = Population()
    population.add(Household("1"))
    population["1"].add(Person("0", freq=1))
    population["1"].add(Person("1", freq=3))
    population.add(Household("2", freq=2))
    assert population.size == 4


def test_population_size_None():
    population = Population()
    population.add(Household("1"))
    population["1"].add(Person("0", freq=1))
    population["1"].add(Person("1", freq=3))
    population.add(Household("2", freq=None))
    assert population.size is None


def test_population_num_households():
    population = Population()
    population.add(Household("1"))
    population["1"].add(Person("0", freq=1))
    population["1"].add(Person("1", freq=3))
    population.add(Household("2"))
    assert population.num_households == 2


def test_population_stats():
    population = Population()
    population.add(Household("1"))
    population["1"].add(Person("0", freq=1))
    population["1"].add(Person("1", freq=3))
    population.add(Household("2"))
    population["2"].add(Person("2", freq=3))
    assert isinstance(population.stats, dict)


def test_population_fix_plans_wrapper(person_heh):
    population = Population()
    population.add(Household("1"))
    population["1"].add(person_heh)
    population.fix_plans()


def test_hh_fix_plans_wrapper(person_heh):
    population = Population()
    population.add(Household("1"))
    population["1"].add(person_heh)
    population["1"].fix_plans()


def test_population_print(capfd, person_heh):
    population = Population()
    population.add(Household("1"))
    population["1"].add(person_heh)
    population.print()
    out, _ = capfd.readouterr()
    assert out


def test_population_sample_locs(person_heh):
    population = Population()
    population.add(Household("1"))
    population["1"].add(person_heh)

    class DummySampler:
        def sample(self, loc, act):
            return None

    population.sample_locs(DummySampler())
    assert population["1"]["1"].plan[2].location.loc is None


def test_set_hh_freq():
    hh = Household("1", freq=None)
    hh.set_freq(1)
    assert hh.freq == 1


def test_av_person_freq():
    hh = Household("1")
    hh.add(Person("1", freq=1))
    hh.add(Person("2", freq=2))
    assert hh.av_person_freq == 1.5


def test_set_person_freq():
    person = Person("1", freq=None)
    person.set_freq(1)
    assert person.freq == 1


def test_av_trip_freq():
    person = Person("1", freq=None)
    person.add(Activity())
    person.add(Leg(freq=1))
    person.add(Activity())
    person.add(Leg(freq=3))
    person.add(Activity())
    assert person.av_trip_freq == 2


def test_av_activity_freq():
    person = Person("1", freq=None)
    person.add(Activity(freq=1))
    person.add(Leg())
    person.add(Activity(freq=2))
    person.add(Leg())
    person.add(Activity(freq=3))
    assert person.av_activity_freq == 2


def test_population_sample_locs_complex(person_heh):
    population = Population()
    population.add(Household("1"))
    population["1"].add(person_heh)

    class DummySampler:
        def sample(self, loc, acty, mode, previous_duration, previous_loc):
            return None

    population.sample_locs_complex(DummySampler())
    assert population["1"]["1"].plan[2].location.loc is None


def test_get_hh_freq_if_None():
    hh = Household("1")
    hh.add(Person("1", freq=None))
    hh.add(Person("2", freq=2))
    assert hh.freq is None


def test_get_hh_freq_mean():
    hh = Household("1")
    hh.add(Person("1", freq=1))
    hh.add(Person("2", freq=3))
    assert hh.freq == 2


def test_get_person_av_freq_from_trips():
    person = Person("1", freq=None)
    person.add(Activity())
    person.add(Leg(freq=1))
    person.add(Activity())
    person.add(Leg(freq=3))
    person.add(Activity())
    assert person.freq == 2


def test_get_person_freq_from_trips():
    person = Person("1", freq=None)
    person.add(Activity())
    person.add(Leg(freq=1))
    person.add(Activity())
    assert person.freq == 1


def test_get_subpopulations():
    pop = Population()
    hh = Household("1")
    hh.add(Person("1", attributes={"subpopulation": "A"}))
    hh.add(Person("2", attributes={"subpopulation": "B"}))
    pop.add(hh)
    hh = Household("2")
    hh.add(Person("1", attributes={"subpopulation": "A"}))
    hh.add(Person("2", attributes={"subpopulation": "C"}))
    pop.add(hh)
    assert pop.subpopulations == {"A", "B", "C"}


def test_get_atributes():
    pop = Population()
    hh = Household("1")
    hh.add(Person("1", attributes={"subpopulation": "A", "age": 10}))
    hh.add(Person("2", attributes={"subpopulation": "B", "age": 20}))
    pop.add(hh)
    hh = Household("2")
    hh.add(Person("1", attributes={"subpopulation": "A", "age": 10}))
    hh.add(Person("2", attributes={"subpopulation": "C", "age": 30}))
    pop.add(hh)
    assert pop.attributes == {"subpopulation": {"A", "B", "C"}, "age": {"10", "20", "30"}}
