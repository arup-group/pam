from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam import modify

import pytest
import random


@pytest.fixture
def person_home_education_home():

    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=mtdt(24 * 60 - 1)
        )
    )

    return person


@pytest.fixture
def home_education_home_education_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_home_work_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'work', 'd'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_shop_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'car', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'car', 'b', 'b'))
    person.add(Activity(2, 'shop', 'b'))
    person.add(Leg(2, 'car', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_home_university_student():

    person = Person(1, attributes={'age': 18, 'job': 'education'})
    person.add(Activity(1, 'home', 'a'))
    person.add(Leg(1, 'bike', 'a', 'b'))
    person.add(Activity(2, 'education', 'b'))
    person.add(Leg(2, 'bike', 'b', 'a'))
    person.add(Activity(3, 'home', 'a'))

    return person


@pytest.fixture
def home_education_shop_education_home():

    person = Person(1)
    person.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(60)))
    person.add(Leg(1, 'car', 'a', 'b', start_time=mtdt(60), end_time=mtdt(70)))
    person.add(Activity(2, 'education', 'b', start_time=mtdt(70), end_time=mtdt(100)))
    person.add(Leg(2, 'bike', 'b', 'c', start_time=mtdt(100), end_time=mtdt(120)))
    person.add(Activity(3, 'shop', 'c', start_time=mtdt(120), end_time=mtdt(180)))
    person.add(Leg(1, 'bike', 'c', 'b', start_time=mtdt(180), end_time=mtdt(200)))
    person.add(Activity(2, 'education', 'b', start_time=mtdt(200), end_time=mtdt(300)))
    person.add(Leg(2, 'car', 'b', 'a', start_time=mtdt(300), end_time=mtdt(310)))
    person.add(Activity(3, 'home', 'a', start_time=mtdt(310), end_time=mtdt(60)))

    return person


def test_home_education_home_removal_of_education_act(person_home_education_home):

    household = Household(1)
    person = person_home_education_home

    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[0].end_time == mtdt(24*60-1)


def test_home_education_home_education_home_removal_of_education_act():

    household = Household(1)
    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=mtdt(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(300),
            end_time=mtdt(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(390),
            end_time=mtdt(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(520),
            end_time=mtdt(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(680),
            end_time=mtdt(24 * 60 - 1)
        )
    )
    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[0].end_time == mtdt(24*60-1)


def test_home_work_home_education_home_removal_of_education_act():

    household = Household(1)
    person = Person(1)
    person.add(
        Activity(
            seq=1,
            act='home',
            area='a',
            start_time=mtdt(0),
            end_time=mtdt(60)
        )
    )
    person.add(
        Leg(
            seq=1,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(60),
            end_time=mtdt(90)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='work',
            area='b',
            start_time=mtdt(90),
            end_time=mtdt(120)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(120),
            end_time=mtdt(180)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(180),
            end_time=mtdt(300)
        )
    )
    person.add(
        Leg(
            seq=3,
            mode='car',
            start_area='a',
            end_area='b',
            start_time=mtdt(300),
            end_time=mtdt(390)
        )
    )
    person.add(
        Activity(
            seq=2,
            act='education',
            area='b',
            start_time=mtdt(390),
            end_time=mtdt(520)
        )
    )
    person.add(
        Leg(
            seq=2,
            mode='car',
            start_area='b',
            end_area='a',
            start_time=mtdt(520),
            end_time=mtdt(580)
        )
    )
    person.add(
        Activity(
            seq=3,
            act='home',
            area='a',
            start_time=mtdt(680),
            end_time=mtdt(24 * 60 - 1)
        )
    )
    household.add(person)

    policy = modify.RemoveActivity(activities=['education'], probability=1)
    policy.apply_to(household)
    assert [p.act for p in household.people['1'].activities] == ['home', 'work', 'home']
    assert household.people['1'].plan[0].start_time == mtdt(0)
    assert household.people['1'].plan[-1].end_time == mtdt(24*60-1)


def test_home_education_home_attribute_based_activity_removal_strict_satisfies_conditions(
        home_education_home_university_student):
    household = Household(1)
    person = home_education_home_university_student
    household.add(person)

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_education(attribute_value):
        return attribute_value == 'education'

    policy_remove_higher_education = modify.RemoveActivity(
        ['education'],
        probability=1,
        attribute_conditions={'age': age_condition_over_17, 'job': job_condition_education},
        strict_conditions=True
    )

    policy_remove_higher_education.apply_to(household)

    for pid, person in household.people.items():
        assert len(person.plan) == 1
        assert isinstance(person.plan.day[0], Activity)


def test_home_education_home_attribute_based_activity_removal_strict_doesnt_satisfy_conditions(
        home_education_home_university_student):
    household = Household(1)
    person = home_education_home_university_student
    household.add(person)

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == 'wasevrrr'

    policy_remove_higher_education = modify.RemoveActivity(
        ['education'],
        probability=1,
        attribute_conditions={'age': age_condition_over_17, 'job': job_condition_wasevrrr},
        strict_conditions=True
    )

    policy_remove_higher_education.apply_to(household)

    for pid, person in household.people.items():
        assert len(person.plan) == 5
        assert isinstance(person.plan.day[2], Activity)
        assert person.plan.day[2].act == 'education'


def test_home_education_home_attribute_based_activity_removal_non_strict_satisfies_condition(
        home_education_home_university_student):
    household = Household(1)
    person = home_education_home_university_student
    household.add(person)

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == 'wasevrrr'

    policy_remove_higher_education = modify.RemoveActivity(
        ['education'],
        probability=1,
        attribute_conditions={'age': age_condition_over_17, 'job': job_condition_wasevrrr},
        strict_conditions=False
    )

    policy_remove_higher_education.apply_to(household)

    for pid, person in household.people.items():
        assert len(person.plan) == 1
        assert isinstance(person.plan.day[0], Activity)

def test_home_education_home_attribute_based_activity_removal_non_strict_doesnt_satisfy_conditions(
        home_education_home_university_student):
    household = Household(1)
    person = home_education_home_university_student
    household.add(person)

    def age_condition_under_0(attribute_value):
        return attribute_value < 0

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == 'wasevrrr'

    policy_remove_higher_education = modify.RemoveActivity(
        ['education'],
        probability=1,
        attribute_conditions={'age': age_condition_under_0, 'job': job_condition_wasevrrr},
        strict_conditions=False
    )

    policy_remove_higher_education.apply_to(household)

    for pid, person in household.people.items():
        assert len(person.plan) == 5
        assert isinstance(person.plan.day[2], Activity)
        assert person.plan.day[2].act == 'education'


def test_remove_second_education_activity(mocker, home_education_shop_education_home):
    mocker.patch.object(modify.RemoveActivity, 'is_selected', side_effect=[False, True])

    person = home_education_shop_education_home
    policy_remove_education = modify.RemoveActivity(['education'], probability=1)
    policy_remove_education.remove_activities(person)

    assert len(person.plan) == 7
    for i in range(0, 7, 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [person.plan.day[i].act for i in range(0, 7, 2)] == ['home', 'education', 'shop', 'home']


def test_activity_is_selected_if_probability_1(mocker):
    mocker.patch.object(random, 'random', side_effect=[0]+[i/10 for i in range(1,10)])

    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=1)
    for i in range(10):
        assert policy_remove_activity.is_selected()


def test_activity_is_selected_when_condition_is_satisfied(mocker):
    mocker.patch.object(random, 'random', return_value=0.5)
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.75)

    assert policy_remove_activity.is_selected()


def test_activity_is_not_selected_when_condition_is_not_satisfied(mocker):
    mocker.patch.object(random, 'random', return_value=0.75)
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.5)

    assert not policy_remove_activity.is_selected()


def test_is_activity_for_removal_activity_matches_RemoveActivity_activities(mocker):
    activity = Activity(act = 'some_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.5)

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_RemoveActivity_activities(mocker):
    activity = Activity(act = 'other_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.5)

    assert not policy_remove_activity.is_activity_for_removal(activity)
