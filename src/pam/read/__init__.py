import pickle

from pam.read.diary import (
    add_hhs_from_hhs_attributes,
    add_hhs_from_persons_attributes,
    add_hhs_from_trips,
    add_persons_from_persons_attributes,
    add_persons_from_trips,
    build_population,
    from_to_travel_diary_read,
    load_travel_diary,
    sample_population,
    tour_based_travel_diary_read,
    trip_based_travel_diary_read,
)
from pam.read.matsim import (
    get_attributes_from_legs,
    get_attributes_from_person,
    load_attributes_map,
    load_attributes_map_from_v12,
    parse_matsim_plan,
    parse_veh_attribute,
    read_matsim,
    selected_plans,
    stream_matsim_persons,
    unpack_leg,
    unpack_leg_v12,
    unpack_route_v11,
)


def load_pickle(path):
    with open(path, "rb") as file:
        return pickle.load(file)
