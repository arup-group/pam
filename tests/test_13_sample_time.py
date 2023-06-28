from datetime import timedelta

from pam.samplers.time import apply_jitter_to_plan, jitter_activity


def test_jitter_activity(Steve):
    jitter_activity(
        plan=Steve.plan, i=0, jitter=timedelta(minutes=5), min_duration=timedelta(minutes=5)
    )
    assert Steve.plan.validate()


def test_jitter_activity_mid_plan(Steve):
    jitter_activity(
        plan=Steve.plan, i=2, jitter=timedelta(minutes=5), min_duration=timedelta(minutes=5)
    )
    assert Steve.plan.validate()


def test_jitter_activity_later_in_plan(Steve):
    jitter_activity(
        plan=Steve.plan, i=4, jitter=timedelta(minutes=5), min_duration=timedelta(minutes=5)
    )
    assert Steve.plan.validate()


def test_apply_jitter_to_plan(Steve):
    apply_jitter_to_plan(
        plan=Steve.plan, jitter=timedelta(minutes=5), min_duration=timedelta(minutes=5)
    )
    assert Steve.plan.validate()
