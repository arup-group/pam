from copy import deepcopy
from datetime import timedelta

from numpy import random

from pam.activity import Plan
from pam.scoring import CharyparNagelPlanScorer
from pam.variables import END_OF_DAY


def reschedule(
    plan: Plan,
    plans_scorer=CharyparNagelPlanScorer,
    config: dict = {},
    horizon: int = 5,
    sensitivity: float = 0.01,
    patience: int = 1000,
):
    best_score = plans_scorer.score_plan(plan, config)
    print(f"Initial best score at iteration 0: {best_score}")
    best_scores = {0: best_score}
    stopper = Stopper(horizon=horizon, sensitivity=sensitivity)
    for n in range(patience):
        proposed_plan = random_mutate_activity_durations(plan, copy=True)
        score = plans_scorer.score_plan(proposed_plan, config)
        if score > best_score:
            print(f"New best score at iteration {n}: {score}")
            best_scores[n] = score
            best_score = score
            plan = proposed_plan
            if not stopper.ok(score):
                return plan, best_scores
    return plan, best_scores


def random_mutate_activity_durations(plan: Plan, copy=True):
    allowance = 24 * 60 * 60  # seconds
    for leg in plan.legs:
        allowance -= leg.duration.total_seconds()
    n_activities = len(list(plan.activities))
    activity_durations = [
        timedelta(seconds=int(random.random() * allowance / n_activities))
        for n in range(n_activities)
    ]
    if copy:
        plan = deepcopy(plan)
    time = plan.day[0].shift_duration(new_duration=activity_durations.pop(0))
    idx = 1
    for activity_duration, leg_duration in zip(
        activity_durations, [leg.duration for leg in plan.legs]
    ):
        time = plan.day[idx].shift_duration(new_start_time=time, new_duration=leg_duration)
        time = plan.day[idx + 1].shift_duration(new_start_time=time, new_duration=activity_duration)
        idx += 2
    plan.day[-1].end_time = END_OF_DAY
    return plan


class Stopper:
    def __init__(self, horizon=5, sensitivity=0.01) -> None:
        self.record = []
        self.horizon = horizon
        self.sensitivity = sensitivity

    def ok(self, score):
        self.record.append(score)
        if len(self.record) > self.horizon:
            self.record.pop(0)
            if self.record[-1] - self.record[0] < self.sensitivity:
                print("Stopping early")
                return False
        return True
