from datetime import timedelta

from pam.array.encode import PlansToCategorical
from pam.read import stream_matsim_persons
from pam.samplers.time import apply_jitter_to_plan


def inf_yield(queue: list):
    while True:
        for i in queue:
            yield i


class ActColour:
    mapping = {"travel": 232}
    _col_queue = [21, 202, 8, 9, 10, 11, 12, 13, 14, 15, 196, 202, 208, 214, 220]
    _bw_queue = [255, 234, 253, 236, 251, 238, 249, 240, 247, 242, 245]

    def __init__(self, colour=True) -> None:
        if colour:
            self._queue = inf_yield(self._col_queue)
        else:
            self._queue = inf_yield(self._bw_queue)

    def paint(self, act, text):
        if act not in self.mapping:
            self.mapping[act] = next(self._queue)
        return f"\033[38;5;{self.mapping[act]}m{text}\033[0m"


def stringify_plans(
    plans_path, simplify_pt_trips: bool = False, crop: bool = False, colour=True, width=101
):
    print(f"Loading plan sequences from {plans_path}.")
    encoder = PlansToCategorical(bin_size=int(86400 / width), duration=86400)
    colourer = ActColour(colour=colour)
    for person in stream_matsim_persons(plans_path, simplify_pt_trips=simplify_pt_trips, crop=crop):
        apply_jitter_to_plan(
            plan=person.plan, jitter=timedelta(minutes=30), min_duration=timedelta(minutes=5)
        )
        encoded = encoder.encode(person.plan)
        string = stringify_plan(plan_array=encoded, mapping=encoder.index_to_act, colourer=colourer)
        print(person.pid, string)

    print()
    print("Key:")
    for act in encoder.act_to_index:
        print(f"{colourer.paint(act, '▇▇▇▇▇▇▇▇▇▇')}: {act}")


def stringify_plan(plan_array, mapping, colourer):
    return "".join([colourer.paint(mapping[i], "▇") for i in plan_array])
