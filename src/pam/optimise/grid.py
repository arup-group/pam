from copy import deepcopy
from datetime import timedelta

from pam.activity import Plan
from pam.scoring import PlanScorer
from pam.variables import START_OF_DAY


class Recorder:
    def __init__(self, initial_score: float, initial_plan: Plan) -> None:
        """Mechanism for recording grid optimiser progress.

        Args:
            initial_score (float): Initial plan score.
            initial_plan (Plan): Initial plan.
        """
        self.best_plan = initial_plan
        self.best_score = initial_score

    def update(self, score: float, plan: Plan):
        """Update with new score and plan.

        Args:
            score (float): Latest plan score.
            plan (Plan): Latest plan.
        """
        if score >= self.best_score:
            self.best_score = score
            self.best_plan = deepcopy(plan)


def grid_search(
    plan: Plan, plans_scorer: PlanScorer, config: dict, step: int = 900, copy=True
) -> (float, Plan):
    """Grid search for optimum plan schedule.

    Checks all permutations of a plan's activity start times and durations, finds plan
    that has maximum score, based on the given scorer. The precision and size of the grid is based
    on the given step (seconds). Smaller steps increase the grid size.

    Trip durations are assumed fixed and activity sequence is not changed.

    Args:
        plan (Plan): Input plan.
        plans_scorer (PlanScorer): Plans scorer object.
        config (Dict): PlansScorer config.
        step (int): Grid size in seconds. Defaults to 900.
        copy (Bool): Create a copy of the input plan. Defaults to True.

    Returns:
        (Plan, float): Best plan found and score of best plan.
    """
    if copy:
        plan = deepcopy(plan)
    initial_score = plans_scorer.score_plan(plan, config)
    recorder = Recorder(initial_score, plan)

    traverse(
        scorer=plans_scorer,
        config=config,
        plan=plan,
        earliest=0,
        step=step,
        leg_index=0,
        recorder=recorder,
    )
    print_report(initial_score, recorder.best_score, step)
    return recorder.best_plan, recorder.best_score


def print_report(initial_score: float, best_score: float, n: int):
    if best_score > initial_score:
        print(f"Score improved from {initial_score} to {best_score} using step size {n}s.")
    else:
        print(f"Failed to improve score from initial {initial_score} using step size {n}s.")


def traverse(
    scorer: PlanScorer,
    config: dict,
    plan: Plan,
    step: int,
    earliest: int,
    leg_index: int,
    recorder: Recorder,
):
    """Traverse all possible grid permutations by enumerating all trip start times of first trip
    and recursively all following trips in sequence.
    """
    ## exit condition
    if leg_index * 2 + 2 >= len(plan):
        recorder.update(scorer.score_plan(plan, cnfg=config), plan)
        return None

    latest_start = latest_start_time(plan, leg_index)
    for earliest in range(earliest, latest_start + step, step):
        activity = plan[leg_index * 2]
        leg = plan[leg_index * 2 + 1]
        next_activity = plan[leg_index * 2 + 2]
        activity.end_time = START_OF_DAY + timedelta(seconds=earliest)
        leg.end_time = leg.shift_start_time(activity.end_time)
        next_activity.start_time = leg.end_time

        traverse(
            scorer=scorer,
            config=config,
            plan=deepcopy(plan),
            earliest=earliest + step,  # + plan[leg_index * 2 + 1].duration.seconds,
            leg_index=leg_index + 1,
            step=step,
            recorder=recorder,
        )


def latest_start_time(plan: Plan, leg_index: int):
    allowance = 24 * 60 * 60
    for c in plan[(leg_index * 2) + 1 :: 2]:
        allowance -= c.duration.seconds
    return allowance
