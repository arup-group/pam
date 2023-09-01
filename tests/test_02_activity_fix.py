from pam.activity import Activity, Leg, Plan
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def test_crop_act_past_end_of_day():
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
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(12000)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12000),
            end_time=mtdt(12020),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(12020), end_time=mtdt(12030)))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_two_acts_past_end_of_day():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(600),
            end_time=mtdt(12020),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(12020), end_time=mtdt(12030)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12030),
            end_time=mtdt(12050),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(12050), end_time=mtdt(12060)))
    plan.crop()
    assert plan.length == 1
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_leg_past_end_of_day():
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
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(1200),
            end_time=mtdt(12020),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(12020), end_time=mtdt(12030)))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_act_out_of_order():
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
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(12000)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12000),
            end_time=END_OF_DAY,
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(12030)))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_leg_out_of_order():
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
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=END_OF_DAY))
    plan.add(
        Leg(
            seq=2, mode="car", start_area="B", end_area="A", start_time=mtdt(0), end_time=END_OF_DAY
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(12030)))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_act_bad_order():
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
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(12000)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12000),
            end_time=mtdt(12020),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(12020), end_time=END_OF_DAY))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_crop_leg_bad_order():
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
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(12000)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12000),
            end_time=mtdt(11000),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(11000), end_time=END_OF_DAY))
    plan.crop()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY


def test_fix_time_consistency():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="A",
            end_area="B",
            start_time=mtdt(610),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=END_OF_DAY))
    plan.fix_time_consistency()
    assert plan[1].start_time == mtdt(600)


def test_fix_location_consistency():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(600),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=END_OF_DAY))
    plan.fix_location_consistency()
    assert plan[1].start_location.area == "A"
    assert plan[1].end_location.area == "B"


def test_plan_fix():
    plan = Plan()
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(0), end_time=mtdt(600)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="B",
            start_time=mtdt(610),
            end_time=mtdt(620),
        )
    )
    plan.add(Activity(seq=3, act="work", area="B", start_time=mtdt(620), end_time=mtdt(12000)))
    plan.add(
        Leg(
            seq=2,
            mode="car",
            start_area="B",
            end_area="A",
            start_time=mtdt(12000),
            end_time=mtdt(11000),
        )
    )
    plan.add(Activity(seq=1, act="home", area="A", start_time=mtdt(11000), end_time=END_OF_DAY))
    plan.fix()
    assert plan.length == 3
    assert plan.day[-1].end_time == END_OF_DAY
    assert plan[1].start_time == mtdt(600)
    assert plan[1].start_location.area == "A"
