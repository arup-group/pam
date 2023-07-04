"""Tests for pam/optimise/grid.py"""
import pytest

from pam.activity import Plan
from pam.optimise import grid


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
