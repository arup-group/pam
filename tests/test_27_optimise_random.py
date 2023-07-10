"""Tests for pam/optimise/random.py"""
import pytest

from pam.optimise import random


@pytest.fixture
def stopper():
    return random.Stopper(horizon=3, sensitivity=0.03)


class TestStopper:
    def test_init(self, stopper):
        assert stopper.record == []
        assert stopper.horizon == 3
        assert stopper.sensitivity == 0.03

    def test_adds_to_record(self, stopper):
        assert stopper.ok(1) is True
        assert stopper.record == [1]

    def test_adds_to_already_populated_record(self, stopper):
        stopper.ok(1)
        stopper.ok(1.02)
        stopper.ok(2)
        assert stopper.record == [1, 1.02, 2]

    def test_pops_oldest_value_when_record_exceeds_horizon_length(self, stopper):
        for i in [1, 2, 3, 4]:
            stopper.ok(i)
        assert stopper.record == [2, 3, 4]

    def test_ok_is_true_when_sensitivity_value_not_breached(self, stopper):
        for i in [1, 2, 3, 4]:
            assert stopper.ok(i) is True

    def test_ok_is_false_when_sensitivity_value_breached_and_record_exceeds_horizon_length(
        self, stopper
    ):
        for i in [1, 2, 2.01]:
            assert stopper.ok(i) is True
        assert stopper.ok(2.02) is False

    def test_pops_oldest_when_sensitivity_value_breached_and_record_exceeds_horizon_length(
        self, stopper
    ):
        for i in [1, 2, 2.01, 2.02]:
            stopper.ok(i)
        assert stopper.record == [2, 2.01, 2.02]
