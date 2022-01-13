from datetime import timedelta
from numpy import random
from copy import deepcopy
from datetime import timedelta

from pam.activity import Plan, Leg, Activity
from pam.variables import END_OF_DAY
from pam.scoring import CharyparNagelPlanScorer


def grid_search(
    plan: Plan,
    plans_scorer = CharyparNagelPlanScorer,
    config : dict = {},
    step : int = 300,
    ):
    best_score = plans_scorer.score_plan(plan, config)
    recorder = Recorder(best_score, plan)

    traverse(
        scorer = plans_scorer,
        config = config,
        plan = plan,
        earliest=0,
        step=step,
        leg_index=0,
        recorder=recorder
        )

    return recorder.best_score, recorder.best_plan


def latest_start_time(plan, leg_index):
    allowance = 24*60*60
    for c in plan[leg_index*2 + 1::2]:
        allowance -= c.duration.seconds
    return allowance


def traverse(scorer, config, plan, step, earliest, leg_index, recorder):

    if leg_index*2+1 == len(plan):
        recorder.update(scorer.score_plan(plan, cnfg=config), plan)
        return None

    latest = latest_start_time(plan, leg_index)
    for start in range(earliest, latest+step, step):
        activity = plan[leg_index*2]
        leg = plan[leg_index*2+1]
        next_activity = plan[leg_index*2+2]
        activity.end_time = activity.start_time + timedelta(seconds=start)
        leg.end_time = leg.shift_start_time(activity.end_time)
        next_activity.start_time = leg.end_time

        traverse(
            scorer = scorer,
            config = config,
            plan = plan,
            earliest = start + plan[leg_index*2+1].duration.seconds,
            leg_index = leg_index+1,
            step = step,
            recorder=recorder
            )


class Recorder():
    def __init__(self, initial_score, initial_plan) -> None:
        self.best_plan = initial_plan
        self.best_score = initial_score

    def update(self, score, plan):
        if score >= self.best_score:
            self.best_score = score
            self.best_plan = deepcopy(plan)
