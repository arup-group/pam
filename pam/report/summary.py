from collections import defaultdict
from enum import Enum

from prettytable import PrettyTable

from pam.core import Population


class TEXT(Enum):
    TITLE = "\n\033[95m\033[4m\033[1m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def header(head: str):
    print(f"{TEXT.HEADER.value}{head}{TEXT.END.value}")


def header_and_text(head: str, text: str):
    print(f"{TEXT.HEADER.value}{head}{TEXT.END.value} {text}")


def subheader_and_text(head: str, text: str):
    print(f"{TEXT.OKBLUE.value}{head}{TEXT.END.value} {text}")


def pretty_print_summary(population: Population, key="subpopulation"):
    # stats
    header("Population Stats:")
    print(stats_summary(population, key))
    print()

    # attributes
    header("Population Attributes:")
    for k, vs in get_attributes(population).items():
        subheader_and_text(f"{k}:", vs)
    print()

    if key is not None:
        for v in population.attributes.get(key, []):
            header(f"Attribute: \033[4m{v}\033[0m:")
            for k, vs in get_attributes(population, key=key, value=v).items():
                subheader_and_text(f"{k}:", vs)
            print()

    # activites
    header("Activities:")
    print(activities_summary(population, key))
    print()

    # modes
    header("Modes:")
    print(modes_summary(population, key))


def print_summary(population: Population, key="subpopulation"):
    # stats
    print("Population Stats:")
    print(stats_summary(population, key))
    print()

    # attributes
    print("Population Attributes:")
    for k, vs in get_attributes(population).items():
        print(f"{k}:", vs)
    print()

    if key is not None:
        for v in population.attributes.get(key, []):
            print(f"Attribute: {v}")
            for k, vs in get_attributes(population, key=key, value=v).items():
                print(f"{k}:", vs)
            print()

    # activites
    print("Activities:")
    print(activities_summary(population, key))
    print()

    # modes
    print("Modes:")
    print(modes_summary(population, key))


def stats_summary(population: Population, key="subpopulation") -> PrettyTable:
    table = PrettyTable()
    summary = {}
    summary["total"] = calc_stats(population)
    slices = []

    if key is not None:
        slices = population.attributes.get(key, [])
        for value in slices:
            summary[value] = calc_stats(population, key, value)

    table.field_names = ["stat", "total"] + list(slices)

    for stat, total_value in summary["total"].items():
        row = [stat, total_value]
        for k in slices:
            row.append(summary[k].get(stat))
        table.add_row(row)

    table.align["stat"] = "r"
    return table


def calc_stats(population: Population, key=None, value=None) -> dict:
    summary = {"hhs": 0, "persons": 0}
    hh_occupants = []
    for _, hh in population:
        if key is not None and value not in hh.get_attribute(key):
            continue
        summary["hhs"] += hh.freq
        occupants = 0
        for _, person in hh:
            if key is not None and not person.attributes.get(key) == value:
                continue
            occupants += 1
            summary["persons"] += person.freq
        hh_occupants.append(occupants)
    if hh_occupants:
        summary["av_occupancy"] = sum(hh_occupants) / len(hh_occupants)
    return summary


# Attributes


def get_attributes(population, show: int = 10, key=None, value=None) -> dict:
    attributes = defaultdict(set)
    for _, _, person in population.people():
        if key is not None and not person.attributes.get(key) == value:
            continue
        for k, v in person.attributes.items():
            if k == key:
                continue
            attributes[k].add(str(v))
    for k, v in attributes.items():
        if len(v) > show:
            attributes[k] = "---"
    return dict(attributes)


# Activites


def activities_summary(population: Population, key="subpopulation") -> PrettyTable:
    table = PrettyTable()
    summary = {}
    summary["total"] = count_activites(population)
    slices = []

    if key is not None:
        slices = population.attributes.get(key, [])
        for value in slices:
            summary[value] = count_activites(population, key, value)

    table.field_names = ["activities", "total"] + list(slices)

    for stat, total_value in summary["total"].items():
        row = [stat, total_value]
        for k in slices:
            row.append(summary[k].get(stat))
        table.add_row(row)

    table.align["activities"] = "r"
    return table


def count_activites(population: Population, key=None, value=None) -> dict:
    classes = population.activity_classes
    summary = {a: 0 for a in classes}
    for _, _, person in population.people():
        if key is not None and not person.attributes.get(key) == value:
            continue
        freq = person.freq
        for act in person.activities:
            summary[act.act] += freq
    return summary


# Modes


def modes_summary(population: Population, key="subpopulation") -> PrettyTable:
    table = PrettyTable()
    summary = {}
    summary["total"] = count_modes(population)
    slices = []

    if key is not None:
        slices = population.attributes.get(key, [])
        for value in slices:
            summary[value] = count_modes(population, key, value)

    table.field_names = ["modes", "total"] + list(slices)

    for stat, total_value in summary["total"].items():
        row = [stat, total_value]
        for k in slices:
            row.append(summary[k].get(stat))
        table.add_row(row)

    table.align["modes"] = "r"

    return table


def count_modes(population: Population, key=None, value=None) -> dict:
    modes = population.mode_classes
    summary = {m: 0 for m in modes}
    for _, _, person in population.people():
        if key is not None and not person.attributes.get(key) == value:
            continue
        freq = person.freq
        for leg in person.legs:
            summary[leg.mode] += freq
    return summary
