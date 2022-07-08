from datetime import timedelta

from pam.read import stream_matsim_persons
from pam.array.encode import plan_to_categorical
from pam.samplers.time import apply_jitter_to_plan


def colour(i, s):
    return f"\033[38;5;{(int(i)*10)+6}m{s}\033[0m"


def print_plans(plans_path):
    print(f"Loading plan sequences from {plans_path}.")
    mapping = {}
    for person in stream_matsim_persons(plans_path):
        apply_jitter_to_plan(
            plan=person.plan,
            jitter=timedelta(minutes=30),
            min_duration=timedelta(minutes=5)
            )
        print(person.pid, stringify_plan(plan_to_categorical(
            person.plan,
            mapping=mapping,
            bin_size=600,
            duration=86400
            )))


def stringify_plan(plan_array):
    return ''.join([colour(i, "▇") for i in plan_array])

