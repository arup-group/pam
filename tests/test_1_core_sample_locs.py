import pytest
from random import random

from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from .fixtures import *


def test_assign_same_locs_to_household(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()
    
    population.sample_locs(FakeSampler())

    home_location = population['1'].location

    for pid, person in SmithHousehold:
        assert person.home == home_location


def test_assign_same_locs_to_person_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()
    
    population.sample_locs(FakeSampler())
    SmithHousehold['3'].plan[2].location == SmithHousehold['3'].plan[6].location


def test_assign_same_locs_to_household_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()
    
    population.sample_locs(FakeSampler())
    SmithHousehold['3'].plan[2].location == SmithHousehold['4'].plan[2].location


def test_assign_same_locs_to_household_escort_activity_in_same_area(SmithHousehold):
    population = Population()
    population.add(SmithHousehold)

    class FakeSampler:
        def sample(self, location_idx, activity):
            return random()
    
    population.sample_locs(FakeSampler())
    SmithHousehold['2'].plan[2].location == SmithHousehold['2'].plan[8].location
    SmithHousehold['2'].plan[2].location == SmithHousehold['4'].plan[2].location
