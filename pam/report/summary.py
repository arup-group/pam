from collections import defaultdict
from prettytable import PrettyTable

from pam.core import Population

class TEXT:
    TITLE = '\n\033[95m\033[4m\033[1m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def yellow(string: str):
    print(f"{TEXT.WARNING}{string}{TEXT.END}")


def red(string: str):
    print(f"{TEXT.FAIL}{string}{TEXT.END}")


def blue(string: str):
    print(f"{TEXT.OKBLUE}{string}{TEXT.END}")


def header(head):
    print(f"{TEXT.HEADER}{head}{TEXT.END}")


def header_and_text(head, text):
    print(f"{TEXT.HEADER}{head}{TEXT.END} {text}")


def subheader_and_text(head, text):
    print(f"{TEXT.OKBLUE}{head}{TEXT.END} {text}")


def fnumber(n: int):
    if n == 0:
        return red(n)
    return str(n)


def print_summary(population: Population, key="subpopulation"):
    # stats
    header("Population Stats:")
    print(stats_summary(population, key))
    print()

    #attributes
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


def stats_summary(population: Population, key="subpopulation") -> PrettyTable:

    table = PrettyTable()
    summary = {}
    summary["total"] = calc_stats(population)
    slices = []

    if key is not None:
        slices =  population.attributes.get(key, [])
        for value in slices:
            summary[value] = calc_stats(population, key, value)

    table.field_names = ["stat", "total"] + list(slices)

    for stat, total_value in summary["total"].items():
        row = [stat, total_value]
        for k in slices:
            row.append(fnumber(summary[k].get(stat)))
        table.add_row(row)

    table.align["stat"] = "r"
    return table


def calc_stats(population: Population, key=None, value=None):
    summary = {
        "hhs": 0,
        "persons": 0,
        }
    hh_occupants = []
    for _, hh in population:
        if key is not None and not hh.get_attribute(key) == value:
            continue
        summary["hhs"] += hh.freq
        occupants = 0
        for _, person in hh:
            occupants += 1
            summary["persons"] += person.freq
        hh_occupants.append(occupants)
    summary["av_occupancy"] = sum(hh_occupants) / summary["hhs"]
    return summary

# Attributes

def get_attributes(population, show:int=10, key=None, value=None) -> dict:
    attributes = defaultdict(set)
    for _, hh in population.households.items():
        if key is not None and not hh.get_attribute(key) == value:
            continue
        for k, v in hh.attributes.items():
            if k == key:
                continue
            attributes[k].add(v)
        for _, p in hh.people.items():
            for k, v in p.attributes.items():
                if k == key:
                    continue
                attributes[k].add(v)
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
        slices =  population.attributes.get(key, [])
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


def count_activites(population: Population, key=None, value=None):
    classes = population.activity_classes
    summary = {a: 0 for a in classes}
    for _, hh in population:
        if key is not None and not hh.get_attribute(key) == value:
            continue
        freq = hh.freq
        for act in hh.activities:
            summary[act.act] += freq
    return summary


# Modes

def modes_summary(population: Population, key="subpopulation") -> PrettyTable:

    table = PrettyTable()
    summary = {}
    summary["total"] = count_modes(population)
    slices = []

    if key is not None:
        slices =  population.attributes.get(key, [])
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


def count_modes(population: Population, key=None, value=None):
    modes = population.mode_classes
    summary = {m: 0 for m in modes}
    for _, hh in population:
        if key is not None and not hh.get_attribute(key) == value:
            continue
        freq = hh.freq
        for leg in hh.legs:
            summary[leg.mode] += hh.freq
    return summary
