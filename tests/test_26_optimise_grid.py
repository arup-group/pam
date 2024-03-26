"""Tests for pam/optimise/grid.py"""

import pytest
from pam.activity import Activity, Leg, Plan
from pam.core import Person
from pam.optimise import grid
from pam.scoring import PlanScorer
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


@pytest.fixture
def recorder():
    return grid.Recorder(0, Plan(home_area="foo"))


class TestRecorder:
    def test_init(self, recorder):
        assert isinstance(recorder.best_plan, Plan)
        assert recorder.best_score == 0

    def test_higher_scoring_plan_updates_best_plan(self, recorder):
        recorder.update(1, Plan(home_area="bar"))
        assert recorder.best_score == 1
        assert recorder.best_plan.home_location.area == "bar"

    def test_lower_scoring_plan_does_not_update_best_plan(self, recorder):
        recorder.update(-1, Plan(home_area="bar"))
        assert recorder.best_score == 0
        assert recorder.best_plan.home_location.area == "foo"

    def test_higher_scoring_plan_deepcopies_best_plan(self, recorder):
        "id() of Plan object and objects within Plan (e.g., `home_location`) change on deepcopy"
        best_plan = Plan(home_area="bar")
        recorder.update(1, best_plan)
        assert id(recorder.best_plan) != id(best_plan)
        assert id(recorder.best_plan.home_location) != id(best_plan.home_location)


@pytest.fixture
def plan():
    plan = Plan()
    plan.day = [
        Activity(act="home", area=1, start_time=mtdt(0), end_time=mtdt(420)),
        Leg(start_time=mtdt(420), end_time=mtdt(480)),
        Activity(act="shop", area=2, start_time=mtdt(480), end_time=mtdt(510)),
        Leg(start_time=mtdt(510), end_time=mtdt(570)),
        Activity(act="work", area=3, start_time=mtdt(570), end_time=mtdt(960)),
        Leg(start_time=mtdt(960), end_time=mtdt(1020)),
        Activity(act="home", area=1, start_time=mtdt(1020), end_time=END_OF_DAY),
    ]
    return plan


def test_latest_start_time(plan):
    assert grid.latest_start_time(plan, 0) == 75600
    assert grid.latest_start_time(plan, 1) == 79200
    assert grid.latest_start_time(plan, 2) == 82800


@pytest.fixture
def dummy_scorer():
    class DummyScorer(PlanScorer):
        def __init__(self, score=0):
            self.score = score

        def score_plan(self, plan: Plan, cnfg: dict, plan_cost=None) -> float:
            return self.score

        def score_person(
            self, person: Person, key: str = "subpopulation", plan_costs=None
        ) -> float:
            return super().score_person(person, key, plan_costs)

    return DummyScorer(1)


def test_traverse_exit(dummy_scorer, plan, recorder):
    assert recorder.best_score == 0
    grid.traverse(dummy_scorer, {}, plan, 1, 0, 3, recorder)
    assert recorder.best_score == 1


def test_traverse_single(dummy_scorer, plan, recorder):
    assert recorder.best_score == 0
    grid.traverse(dummy_scorer, {}, plan, 7200, 72000, 2, recorder)
    assert recorder.best_score == 1


def test_traverse_double(dummy_scorer, plan, recorder):
    assert recorder.best_score == 0
    grid.traverse(dummy_scorer, {}, plan, 7200, 72000, 1, recorder)
    assert recorder.best_score == 1
