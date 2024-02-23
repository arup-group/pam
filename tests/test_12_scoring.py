import pytest
from pam.read import read_matsim
from pam.scoring import CharyparNagelPlanScorer

TEST_EXPERIENCED_PLANS_PATH = pytest.test_data_dir / "test_matsim_experienced_plans_v12.xml"


def test_score_plan_monetary_cost(default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    plan_cost = 20
    result = scorer.score_plan_monetary_cost(plan_cost, default_config)
    assert result == 20


def test_score_day_mode_use(default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    mode = "car"
    result = scorer.score_day_mode_use(mode, default_config)
    assert result == -2


def test_travel_time_score(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.travel_time_score(default_leg, default_config)
    assert result == -1


def test_mode_constant_score(default_config, car_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.mode_constant_score(car_leg, default_config)
    assert result == -1


def test_travel_distance_score(default_config, car_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.travel_distance_score(car_leg, default_config)
    assert result == -5.0024999999999995


def test_score_leg(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    pt_waiting_time_score = 0
    mode_constant_score = 0
    travel_time_score = -1
    travel_distance_score = 0
    expected = (
        pt_waiting_time_score + mode_constant_score + travel_time_score + travel_distance_score
    )
    result = scorer.score_leg(default_leg, default_config)
    assert result == expected


def test_too_short_score(default_config, short_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.too_short_score(short_activity, default_config)
    assert result == -5


def test_early_departure_score(default_config, short_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.early_departure_score(short_activity, default_config)
    assert result == -5


def test_late_arrival_score(default_config, late_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.late_arrival_score(late_activity, default_config)
    assert result == -27


def test_pt_waiting_time_score(default_config, pt_wait_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    # 5 minutes wait time
    result = scorer.pt_waiting_time_score(pt_wait_leg, default_config)
    assert result == -0.16666666666666666


def test_score_person(config, Anna):
    scorer = CharyparNagelPlanScorer(cnfg=config)
    result = scorer.score_person(Anna)
    assert result == 122.46037078518998


def test_summary(config, Anna):
    scorer = CharyparNagelPlanScorer(cnfg=config)
    try:
        scorer.print_summary(Anna)
    except (RuntimeError, TypeError, NameError, OSError, ValueError):
        pytest.fail("Error")


def test_score_plan(Anna, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan(Anna.plan, default_config)
    assert result == 122.46037078518998


def test_score_plan_daily(Anna, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan(Anna.plan, default_config)
    assert result == 122.46037078518998


def test_score_plan_activities(Anna, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan_activities(Anna.plan, default_config)
    assert result == 134.46037078518998


def test_score_small_plan_activity(small_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan_activities(small_plan, default_config)
    # 24-hr home activity
    assert result == 121.90659700031607


def test_duration_score(default_config, short_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.duration_score(short_activity, default_config)
    assert result == -2.0709270877371857


def test_waiting_score(default_config, early_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.waiting_score(early_activity, default_config)
    assert result == -2


def test_score_pt_interchanges(AnnaPT, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_pt_interchanges(AnnaPT.plan, default_config)
    assert result == -1


def test_scores_experienced(config_complex):
    """Test calculated scores against MATSim experienced plan scores."""
    population = read_matsim(TEST_EXPERIENCED_PLANS_PATH, version=12, crop=False)
    scorer = CharyparNagelPlanScorer(config_complex)
    for hid, pid, person in population.people():
        if "subpopulation" not in person.attributes:
            person.attributes["subpopulation"] = "default"
        matsim_score = person.plan.score
        pam_score = scorer.score_person(person)
        assert abs(matsim_score - pam_score) < 0.1
