from random import random

from pam.core import Population
from pam.location import Location
from shapely.geometry import Point


def test_assign_same_locs_to_household(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()

    population.sample_locs(FakeSampler())

    home_location = population[1].location

    for pid, person in SmithHousehold:
        assert person.home == home_location


def test_assign_same_locs_to_person_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()

    population.sample_locs(FakeSampler())
    SmithHousehold[3].plan[2].location == SmithHousehold[3].plan[6].location


def test_assign_same_locs_to_household_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()

    population.sample_locs(FakeSampler())
    SmithHousehold[3].plan[2].location == SmithHousehold[4].plan[2].location


def test_assign_same_locs_to_household_escort_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()

    population.sample_locs(FakeSampler())
    SmithHousehold[2].plan[2].location == SmithHousehold[2].plan[8].location
    SmithHousehold[2].plan[2].location == SmithHousehold[4].plan[2].location


def test_retain_already_existing_locs(SmithHousehold):
    """The sampler does."""
    population = Population()
    population.add(SmithHousehold)
    existing_location = Location(area="w", loc=Point(1, 1))

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()

    # keeps existing location, otherwise it samples
    SmithHousehold[2].plan[2].location = existing_location
    population.sample_locs(FakeSampler(), location_override=False)
    for pid, person in SmithHousehold:
        for i, act in enumerate(person.activities):
            if pid == 2 and i == 1:
                assert act.location == existing_location
            else:
                assert isinstance(act.location.loc, float)

    # default behaviour is to override
    population.sample_locs(FakeSampler())
    assert SmithHousehold[2].plan[2].location != existing_location
