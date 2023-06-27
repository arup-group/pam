import pickle

from pam.read.diary import load_travel_diary
from pam.read.matsim import (
    get_attributes_from_legs,
    get_attributes_from_person,
    load_attributes_map,
    load_attributes_map_from_v12,
    parse_matsim_plan,
    read_all_vehicles_file,
    read_electric_vehicles_file,
    read_matsim,
    read_vehicles,
    selected_plans,
    stream_matsim_persons,
    unpack_leg,
    unpack_leg_v12,
    unpack_route_v11,
)


def load_pickle(path):
    with open(path, "rb") as file:
        return pickle.load(file)
