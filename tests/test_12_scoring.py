import pytest
from pam.activity import Activity, Leg
from pam.core import Person
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam.scoring import CharyparNagelPlanScorer

@pytest.fixture()
def default_config():
    return {
        'mUM': 1,
        'utilityOfLineSwitch': -1,
        'performing': 6,
        'waiting': -1,
        'waitingPt': -2,
        'lateArrival': -18,
        'earlyDeparture': -1,
        'work': {
            'typicalDuration': '08:30:00',
            'openingTime': '06:00:00',
            'closingTime': '20:00:00',
            'latestStartTime': '09:30:00',
            'earliestEndTime': '16:00:00',
            "minimalDuration": "08:00:00"
            },
        "education": {
            "typicalDuration": "06:00:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
            "minimalDuration": "01:00:00"
        },
        'home': {
            'typicalDuration': '12:00:00',
            "minimalDuration": "08:00:00"
            },
        'shop': {
            'typicalDuration': '00:30:00',
            "minimalDuration": "00:10:00"
            },
        'car': {
            'constant': -0,
            'dailyMonetaryConstant': -0,
            'dailyUtilityConstant': -0,
            'marginalUtilityOfDistance': -0,
            'marginalUtilityOfTravelling': -5,
            'monetaryDistanceRate': -0.0005
            },
        'pt': {
            'marginalUtilityOfTravelling': -5,
            'monetaryDistanceRate': -0.001
            },
        'bus': {
            'marginalUtilityOfTravelling': -5,
            'monetaryDistanceRate': -0.001
            },
        'train': {
            'marginalUtilityOfTravelling': -5,
            'monetaryDistanceRate': -0.001
            },
        'walk': {
            'marginalUtilityOfTravelling': -12,
            },
        'bike': {
            'marginalUtilityOfTravelling': -12,
            }
        }


@pytest.fixture()
def config():
    # includes the default name
    return {
        "default": {
            'mUM': 1,
            'utilityOfLineSwitch': -1,
            'performing': 6,
            'waiting': 0,
            'waitingPt': -2,
            'lateArrival': -18,
            'earlyDeparture': -0,
            'work': {
                'typicalDuration': '08:30:00',
                'openingTime': '06:00:00',
                'closingTime': '20:00:00',
                'latestStartTime': '09:30:00',
                'earliestEndTime': '16:00:00',
                "minimalDuration": "08:00:00"
                },
            "education": {
                "typicalDuration": "06:00:00",
                "openingTime": "06:00:00",
                "closingTime": "20:00:00",
                "minimalDuration": "01:00:00"
            },
            'home': {
                'typicalDuration': '12:00:00',
                "minimalDuration": "08:00:00"
                },
            'shop': {
                'typicalDuration': '00:30:00',
                "minimalDuration": "00:10:00"
                },
            'car': {
                'constant': -0,
                'dailyMonetaryConstant': -0,
                'dailyUtilityConstant': -0,
                'marginalUtilityOfDistance': -0,
                'marginalUtilityOfTravelling': -5,
                'monetaryDistanceRate': -0.0005
                },
            'pt': {
                'marginalUtilityOfTravelling': -5,
                'monetaryDistanceRate': -0.001
                },
            'bus': {
                'marginalUtilityOfTravelling': -5,
                'monetaryDistanceRate': -0.001
                },
            'train': {
                'marginalUtilityOfTravelling': -5,
                'monetaryDistanceRate': -0.001
                },
            'walk': {
                'marginalUtilityOfTravelling': -12,
                },
            'bike': {
                'marginalUtilityOfTravelling': -12,
                }
            }
        }



@pytest.fixture()
def default_leg():
    default_leg = Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5), distance=5)
    return default_leg

@pytest.fixture()
def short_activity():
    short_activity = Activity(2, 'work', 'b', start_time=mtdt(8 * 60), end_time=mtdt(11 * 60))
    return short_activity


@pytest.fixture()
def late_activity():
    late_activity = Activity(2, 'work', 'b', start_time=mtdt(11 * 60), end_time=mtdt(18 * 60))
    return late_activity


@pytest.fixture()
def default_plan():
    Anna = Person(4, attributes={'age': 6, 'job': 'education', 'gender': 'female', 'subpopulation': 'default'})
    Anna.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Anna.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30), distance=5))
    Anna.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Anna.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30), distance=5))
    Anna.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    default_plan = Anna.plan
    return default_plan


@pytest.fixture()
def Anna():
    Anna = Person(4, attributes={'age': 6, 'job': 'education', 'gender': 'female', 'subpopulation':'default'})
    Anna.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Anna.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30), distance=5))
    Anna.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Anna.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30), distance=5))
    Anna.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 30), end_time=END_OF_DAY))
    return Anna

@pytest.fixture()
def early_activity():
    early_activity = Activity(2, 'work', 'b', start_time=mtdt(4 * 60), end_time=mtdt(11 * 60))
    return early_activity


@pytest.fixture()
def small_plan():
    Henry = Person(4, attributes={'age': 6, 'job': 'education', 'gender': 'male', 'subpopulation': 'subpopulation'})
    Henry.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(24 * 60)))
    small_plan = Henry.plan
    return small_plan


def test_score_plan_monetary_cost(default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    plan_cost = 20
    result = scorer.score_plan_monetary_cost(plan_cost, default_config)
    assert result == 20


def test_score_day_mode_use(default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    mode = 'car'
    result = scorer.score_day_mode_use(mode, default_config)
    assert result == 0


def test_travel_time_score(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.travel_time_score(default_leg, default_config)
    assert result == -1


def test_mode_constant_score(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.mode_constant_score(default_leg, default_config)
    assert result == 0


def test_travel_distance_score(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.travel_distance_score(default_leg, default_config)
    assert result == 0


def test_score_leg(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    pt_waiting_time_score = 0
    mode_constant_score = 0
    travel_time_score = -1
    travel_distance_score = 0
    expected = pt_waiting_time_score + mode_constant_score + travel_time_score + travel_distance_score
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
    result = scorer.early_departure_score(late_activity, default_config)
    assert result == 0


def test_pt_waiting_time_score(default_config, default_leg):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.pt_waiting_time_score(default_leg, default_config)
    assert result == 0


def test_score_person(config, Anna):
    scorer = CharyparNagelPlanScorer(cnfg=config)
    result = scorer.score_person(Anna)
    assert result == 122.46037078518998


def test_summary(config, Anna):
    scorer = CharyparNagelPlanScorer(cnfg=config)
    try:
        scorer.summary(Anna)
    except (RuntimeError, TypeError, NameError, OSError, ValueError):
        pytest.fail("Error")


def test_score_plan(default_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan(default_plan, default_config)
    assert result == 122.46037078518998


def test_score_plan_daily(default_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan(default_plan, default_config)
    assert result == 122.46037078518998


def test_score_plan_activities(default_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan_activities(default_plan, default_config)
    assert result == 134.46037078518998


def test_score_small_plan_activity(small_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_plan_activities(small_plan, default_config)
    assert result == -116.92968471643337


def test_duration_score(default_config, short_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.duration_score(short_activity, default_config)
    assert result == -2.3822907838409333


def test_waiting_score(default_config, early_activity):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.waiting_score(early_activity, default_config)
    assert result == -2


def test_score_pt_interchanges(default_plan, default_config):
    scorer = CharyparNagelPlanScorer(cnfg=default_config)
    result = scorer.score_pt_interchanges(default_plan, default_config)
    assert result == 0
