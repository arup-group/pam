"""Tests for pam/optimise/random.py"""

import pytest
from pam.activity import Activity, Leg, Plan
from pam.core import Person
from pam.optimise import random
from pam.scoring import PlanScorer
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


@pytest.fixture
def stopper():
    return random.Stopper(horizon=3, sensitivity=0.03)


class TestStopper:
    def test_init(self, stopper):
        assert stopper.record == []
        assert stopper.horizon == 3
        assert stopper.sensitivity == 0.03

    def test_adds_to_record(self, stopper):
        assert stopper.stop(1) is False
        assert stopper.record == [1]

    def test_adds_to_already_populated_record(self, stopper):
        stopper.stop(1)
        stopper.stop(1.02)
        stopper.stop(2)
        assert stopper.record == [1, 1.02, 2]

    def test_pops_oldest_value_when_record_exceeds_horizon_length(self, stopper):
        for i in [1, 2, 3, 4]:
            stopper.stop(i)
        assert stopper.record == [2, 3, 4]

    def test_ok_is_true_when_sensitivity_value_not_breached(self, stopper):
        for i in [1, 2, 3, 4]:
            assert stopper.stop(i) is False

    def test_ok_is_false_when_sensitivity_value_breached_and_record_exceeds_horizon_length(
        self, stopper
    ):
        for i in [1, 2, 2.01]:
            assert stopper.stop(i) is False
        assert stopper.stop(2.02) is True

    def test_pops_oldest_when_sensitivity_value_breached_and_record_exceeds_horizon_length(
        self, stopper
    ):
        for i in [1, 2, 2.01, 2.02]:
            stopper.stop(i)
        assert stopper.record == [2, 2.01, 2.02]


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


def test_random_mutate_activity_durations_return_valid_sequence(plan):
    for _ in range(10):
        plan = random.random_mutate_activity_durations(plan, copy=False)
        assert plan.valid_sequence
        assert plan.valid_time_sequence


@pytest.fixture
def dummy_scorer():
    class DummyScorer(PlanScorer):
        def __init__(self, score=0):
            self.score = score

        def score_plan(self, plan: Plan, cnfg: dict, plan_cost=None) -> float:
            self.score += 1
            return self.score - 1

        def score_person(
            self, person: Person, key: str = "subpopulation", plan_costs=None
        ) -> float:
            return super().score_person(person, key, plan_costs)

    return DummyScorer(1)


def test_reschedule_no_patience(dummy_scorer, plan):
    # 0 patience is actually one iteration
    new_plan, best_scores = random.reschedule(plan, dummy_scorer, {}, patience=0)
    assert best_scores == {0: 2}
    assert new_plan.valid_sequence
    assert new_plan.valid_time_sequence


def test_reschedule(dummy_scorer, plan):
    new_plan, best_scores = random.reschedule(plan, dummy_scorer, {}, patience=2)
    assert best_scores == {0: 2, 1: 3, 2: 4}
    assert new_plan.valid_sequence
    assert new_plan.valid_time_sequence
