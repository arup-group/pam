"""Methods for cropping plans outside core areas."""

from typing import List

from shapely.geometry import LineString, Polygon

import pam
from pam.activity import Activity, Leg, Plan
from pam.core import Population
from pam.variables import END_OF_DAY, START_OF_DAY


def simplify_population(
    population: str,
    boundary: str,
    snap_to_boundary: bool = False,
    rename_external_activities: bool = False,
) -> None:
    """Simplify external plans across a population."""
    # simplify plans
    for hid, pid, person in population.people():
        simplify_external_plans(person.plan, boundary, snap_to_boundary, rename_external_activities)

    # remove empty person-plans and households
    remove_persons = []
    for hid, pid, person in population.people():
        if len(person.plan) == 1 and person.plan.day[0].act == "external":
            remove_persons.append((hid, pid))
    for hid, pid in remove_persons:
        del population[hid].people[pid]

    remove_hhs = [
        hid for hid in population.households if len(population.households[hid].people) == 0
    ]
    for hid in remove_hhs:
        del population.households[hid]


def simplify_external_plans(
    plan: Plan,
    boundary: Polygon,
    snap_to_boundary: bool = False,
    rename_external_activities: bool = False,
) -> None:
    """Simplify any activities happening outside the boundary area.

    Method:
     1. Identify which legs touch the boundary area
     2. Keep the relevant legs/activities and drop the remaining components
     3. Infill: create any new legs between external activities as necessary
     4. Ensure plan consistency: start/end times, sequences, etc
     5. **optional** Rename activities to "external"
     6. **optional** Crop the leg geometries to start/stop at the core area boundaries

    Args:
      plan (Plan): a PAM plan
      boundary (Polygon): the geometry of the core modelled area
      snap_to_boundary (bool, optional): whether to crop legs to stop at the core area boundary. Defaults to False.
      rename_external_activities (bool, optional): whether to rename all external-area activities as "external" Defaults to False.

    """
    link_plan(plan)
    kept_activities = get_kept_activities(plan, boundary)  # activities to keep
    crop_plan(plan, kept_activities)  # drop external plan components
    infill_legs(plan)  # infill with any new legs if required
    stretch_times(plan)  # fix plan time boundaries
    link_plan(plan)  # re-link plan components
    if rename_external_activities:
        rename_external(plan, boundary)  # rename activities to "external"
    if snap_to_boundary:
        for leg in plan.legs:
            crop_leg(leg, boundary)  # crop leg geometry


def get_leg_path(leg: Leg) -> LineString:
    """Get the (euclidean) geometry of a leg."""
    path = LineString([leg.start_location.loc, leg.end_location.loc])
    return path


def leg_intersects(leg: Leg, boundary: Polygon) -> bool:
    """Check whether a leg touches an area defined by a boundary."""
    path = get_leg_path(leg)
    return path.intersects(boundary)


def crop_leg(leg: Leg, boundary: Polygon) -> None:
    """Crop a leg to a boundary."""
    path = get_leg_path(leg)
    path_cropped = path.intersection(boundary)
    start_location, end_location = path_cropped.boundary.geoms
    leg.start_location.loc = start_location
    leg.previous.location.loc = start_location
    leg.end_location.loc = end_location
    leg.next.location.loc = end_location


def get_kept_activities(plan: Plan, boundary: Polygon) -> list:
    """Get a list of the activities to keep after cropping external-external movements."""
    kept_activities = list()
    for leg in plan.legs:
        if leg_intersects(leg, boundary):
            for act in [leg.previous, leg.next]:
                if act not in kept_activities:
                    kept_activities.append(act)
    return kept_activities


def filter_component(component, kept_activities: List[Activity]) -> bool:
    """Check if an activity/leg should be kept."""
    if isinstance(component, Activity):
        return component in kept_activities
    elif isinstance(component, Leg):
        return (component.previous in kept_activities) and (component.next in kept_activities)


def crop_plan(plan: Plan, kept_activities: List[Activity]) -> None:
    """Crop a plan in a way that exludes any external-external movement (and the corresponding activities).
    If no plan components are left in scope, the plan will have a single "external" activity.
    """
    if kept_activities:
        day = list(filter(lambda x: filter_component(x, kept_activities), plan.day))
    else:
        day = empty_day()
    plan.day = day


def empty_day() -> list:
    day = [
        Activity(
            seq=1,
            act="external",
            area="external",
            start_time=pam.utils.minutes_to_datetime(0),
            end_time=pam.variables.END_OF_DAY,
        )
    ]
    return day


def create_leg(previous_act: Activity, next_act: Activity, travel_mode: str = "car") -> Leg:
    """Create a leg between two activities."""
    leg = Leg(
        start_time=previous_act.end_time,
        end_time=next_act.start_time,
        mode=travel_mode,
        purp=next_act.act,
    )
    leg.start_location = previous_act.location
    leg.end_location = next_act.location
    # link
    leg.previous = previous_act
    leg.next = next_act
    return leg


def infill_legs(plan: Plan) -> None:
    """Infill missing legs.
    If there is no leg between two activities, a new one is created linking them.
    """
    i = 0
    while i < len(plan.day) - 1:
        component1 = plan.day[i]
        component2 = plan.day[i + 1]
        if isinstance(component1, Activity) and isinstance(component2, Activity):
            leg = create_leg(component1, component2)
            plan.day.insert(i + 1, leg)
            i += 1
        i += 1


def stretch_times(plan: Plan) -> None:
    """Extend start/end activity times to the start/end of day."""
    plan.day[0].start_time = START_OF_DAY
    plan.day[-1].end_time = END_OF_DAY


def rename_external(plan: Plan, boundary: Polygon) -> None:
    """Rename all external-area activities as "external"."""
    for act in plan.activities:
        if not boundary.contains(act.location.loc):
            act.act = "external"


# helpers ###########################################


def list_get(list_to_access, idx):
    if idx < len(list_to_access) and idx >= 0:
        return list_to_access[idx]
    else:
        return None


def link_plan(plan: Plan) -> None:
    """Link a plan: each activity/leg gets a pointer to the previous/next plan component."""
    plan_list = list(plan)
    act_list = list(plan.activities)
    leg_list = list(plan.legs)

    for i, p in enumerate(plan_list):
        p.next = list_get(plan_list, i + 1)
        p.previous = list_get(plan_list, i - 1)

    for i, p in enumerate(act_list):
        p.next_act = list_get(act_list, i + 1)
        p.previous_act = list_get(act_list, i - 1)

    for i, p in enumerate(leg_list):
        p.start_hour = p.start_time.hour
        p.next_leg = list_get(leg_list, i + 1)
        p.previous_leg = list_get(leg_list, i - 1)
        p.start_location = p.previous.location
        p.end_location = p.next.location


def link_population(population: Population) -> None:
    """Link the plan components of every agent in the population."""
    for hid, pid, person in population.people():
        link_plan(person.plan)
