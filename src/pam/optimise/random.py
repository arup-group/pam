from copy import deepcopy
from datetime import timedelta

from numpy import random

from pam.activity import Plan
from pam.scoring import PlanScorer
from pam.variables import END_OF_DAY


def reschedule(
    plan: Plan,
    plans_scorer: PlanScorer,
    config: dict = {},
    horizon: int = 5,
    sensitivity: float = 0.01,
    patience: int = 1000,
) -> (Plan, float):
    """Randomly search for an improved plan sequence based on given plans_scorer.

    This is not seriously suggested as a sensible approach, it is supplied for example only.

    Args:
        plan (Plan): Input plan.
        plans_scorer (PlanScorer): Plans scorer.
        config (dict): plans_scorer configuration. Defaults to {}.
        horizon (int): Early stopper horizon. Defaults to 5.
        sensitivity (float): Early stopper sensitivity. Defaults to 0.01.
        patience (int): Defaults to 1000.

    Returns:
        (Plan, float): best plan found and best score.
    """
    best_score = plans_scorer.score_plan(plan, config)
    initial_score = best_score
    best_scores = {0: best_score}
    stopper = Stopper(horizon=horizon, sensitivity=sensitivity)
    for n in range(patience + 1):
        proposed_plan = random_mutate_activity_durations(plan, copy=True)
        score = plans_scorer.score_plan(proposed_plan, config)
        if score > best_score:
            best_scores[n] = score
            best_score = score
            plan = proposed_plan
            if stopper.stop(score):
                print_report(initial_score, best_score, n)
                return plan, best_scores
    print_report(initial_score, best_score, n)
    return plan, best_scores


def print_report(initial_score, best_score, n):
    if best_score > initial_score:
        print(f"Score improved from {initial_score} to {best_score} in {n} steps.")
    else:
        print(f"Failed to improve score from initial {initial_score} in {n} steps.")


def random_mutate_activity_durations(plan: Plan, copy=True):
    """Rearrange input plan into random new plan, maintaining activity sequence and trip durations."""
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
        """Early stopping mechanism. Maintains last n scores, where n is equal to "horizon".
        Triggers an early stop if change across horizon is less than given sensitivity.

        Args:
            horizon (int, optional): length of stored history. Defaults to 5.
            sensitivity (float, optional): stopping tolerance. Defaults to 0.01.
        """
        self.record = []
        self.horizon = horizon
        self.sensitivity = sensitivity

    def stop(self, score):
        self.record.append(score)
        if len(self.record) > self.horizon:
            self.record.pop(0)
            if abs(self.record[-1] - self.record[0]) < self.sensitivity:
                return True
        return False
