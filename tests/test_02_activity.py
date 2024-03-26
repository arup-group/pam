import pytest
from pam.activity import Activity, Leg, Plan
from pam.utils import minutes_to_datetime as mtdt


@pytest.fixture()
def list_of_acts():
    a_1 = Activity(2, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act_2", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_3 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_4 = Activity(2, "act", "loc_2", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_5 = Activity(1, "_act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_6 = Activity(2, "act", "loc", start_time=mtdt(18 * 60 + 1), end_time=mtdt(19 * 60))
    return [a_1, a_2, a_3, a_4, a_5, a_6]


def test_Activities_are_exact():
    a_1 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert a_1.is_exact(a_2)


def test_Activities_act_differ_and_are_not_exact():
    a_1 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act_2", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_loc_differ_and_are_not_exact():
    a_1 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act", "loc_2", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_start_time_differ_and_are_not_exact():
    a_1 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act", "loc", start_time=mtdt(18 * 60 + 1), end_time=mtdt(19 * 60))

    assert not a_1.is_exact(a_2)


def test_Activities_end_time_differ_and_are_not_exact():
    a_1 = Activity(1, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60))
    a_2 = Activity(2, "act", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60 + 1))

    assert not a_1.is_exact(a_2)


def test_activity_in_list_exact(list_of_acts):
    assert list_of_acts[2].isin_exact(list_of_acts)


def test_very_similar_activity_in_list_exact(list_of_acts):
    v_similar_act = Activity(
        9999999, "act_2", "loc", start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)
    )
    assert v_similar_act.isin_exact(list_of_acts)


def test_activity_with_different_times_not_in_list_exact(list_of_acts):
    different_times_act = Activity(
        2, "act_2", "loc", start_time=mtdt(18 * 60 + 999), end_time=mtdt(19 * 60 + 999)
    )
    assert not different_times_act.isin_exact(list_of_acts)


def test_activity_with_different_times_in_list(list_of_acts):
    different_times_act = Activity(
        2, "act_2", "loc", start_time=mtdt(18 * 60 + 999), end_time=mtdt(19 * 60 + 999)
    )
    assert different_times_act in list_of_acts


def test_mode_and_activity_classes():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    assert plan.activity_classes == set(["home", "work"])
    assert plan.mode_classes == set(["car"])


def test_get_component():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    assert plan.get(0).act == "home"
    assert plan.get(4) is None
    assert plan.get(4, "1") == "1"


def test_return_first_act_as_home_act_if_missing():
    plan = Plan()
    plan.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))
    assert plan.home == "A"


def test_compare_plans_equal():
    plana = Plan()
    plana.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plana.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plana.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    planb = Plan()
    planb.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    planb.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    planb.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    assert plana == planb


def test_compare_plans_not_equal():
    plana = Plan()
    plana.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plana.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plana.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    planb = Plan()
    planb.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(800)))
    planb.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(800),
            end_time=mtdt(620),
        )
    )
    planb.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    assert not plana == planb


def test_compare_plans_not_equal_types():
    plana = Plan()
    plana.add(Activity(seq=1, act="work", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plana.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plana.add(Activity(seq=3, act="shop", area="B", start_time=mtdt(620), end_time=mtdt(1200)))

    with pytest.raises(UserWarning, match=r"Cannot compare plan to non plan"):
        assert plana == "foo"


def test_add_wrong_type():
    plan = Plan()
    with pytest.raises(UserWarning):
        plan.add(None)
