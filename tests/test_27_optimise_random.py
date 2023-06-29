"""Tests for pam/optimise/random.py"""
import pytest

from pam.optimise import random


@pytest.fixture
def stopper():
    return random.Stopper(horizon=3, sensitivity=0.03)


class TestStopper:
    def test_stopper_init(self, stopper):
        assert stopper.record == []
        assert stopper.horizon == 3
        assert stopper.sensitivity == 0.03

    def test_stopper_ok_1(self, stopper):
        assert stopper.ok(1) is True
        assert stopper.record == [1]

    def test_stopper_ok_2(self, stopper):
        assert stopper.ok(1) is True
        assert stopper.ok(1.02) is True
        assert stopper.record == [1, 1.02]

    def test_stopper_ok_3_no_stop(self, stopper):
        for i in [1, 2, 3, 4]:
            assert stopper.ok(i) is True
        assert stopper.record == [2, 3, 4]

    def test_stopper_ok_3_stop(self, stopper):
        for i in [1, 2, 2.01]:
            assert stopper.ok(i) is True
        assert stopper.ok(2.02) is False
        assert stopper.record == [2, 2.01, 2.02]
