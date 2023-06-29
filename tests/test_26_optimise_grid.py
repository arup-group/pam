"""Tests for pam/optimise/grid.py"""
import pytest

from pam.activity import Plan
from pam.optimise import grid


@pytest.fixture
def recorder():
    return grid.Recorder(0, Plan(home_area="foo"))


class TestRecorder:
    def test_recorder_init(self, recorder):
        assert isinstance(recorder.best_plan, Plan)
        assert recorder.best_score == 0

    def test_recorder_do_update(self, recorder):
        recorder.update(1, Plan(home_area="bar"))
        assert recorder.best_score == 1
        assert recorder.best_plan.home_location.area == "bar"

    def test_recorder_do_not_update(self, recorder):
        recorder.update(-1, Plan(home_area="bar"))
        assert recorder.best_score == 0
        assert recorder.best_plan.home_location.area == "foo"
