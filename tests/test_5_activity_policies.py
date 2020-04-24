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
    person.add(Leg(3, 'bike', 'c', 'b', start_time=mtdt(180), end_time=mtdt(200)))
    person.add(Activity(4, 'education', 'b', start_time=mtdt(200), end_time=mtdt(300)))
    person.add(Leg(4, 'car', 'b', 'a', start_time=mtdt(300), end_time=mtdt(310)))
    person.add(Activity(5, 'home', 'a', start_time=mtdt(310), end_time=mtdt(24 * 60 - 1)))

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
        attribute_strict_conditions=True
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
        attribute_strict_conditions=True
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
        attribute_strict_conditions=False
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
        attribute_strict_conditions=False
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
    policy_remove_education.remove_individual_activities(person)

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


def test_is_activity_for_removal_activity_matches_RemoveActivity_activities():
    activity = Activity(act = 'some_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.5)

    assert policy_remove_activity.is_activity_for_removal(activity)


def test_is_activity_for_removal_activity_does_not_match_RemoveActivity_activities():
    activity = Activity(act = 'other_activity')
    policy_remove_activity = modify.RemoveActivity(['some_activity'], probability=0.5)

    assert not policy_remove_activity.is_activity_for_removal(activity)


def test_remove_activities_removes_second_activity(home_education_shop_education_home):
    person = home_education_shop_education_home
    modify.remove_activities(person, [2], default='home')

    assert len(person.plan) == 7
    for i in range(0, 7, 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [person.plan.day[i].act for i in range(0, 7, 2)] == ['home', 'shop', 'education', 'home']


def test_remove_selected_activities_delegates_right_indices_to_remove_activity_when_one_activity_selected(mocker):
    mocker.patch.object(modify, 'remove_activities')
    person = home_education_shop_education_home

    activities = [False, False, False, True, False]
    modify.remove_selected_activities(person, activities, default='home')

    modify.remove_activities.assert_called_once_with(person, [6], 'home')


def test_remove_selected_activities_delegates_right_indices_to_remove_activity_when_activities_index_shifts(mocker):
    mocker.patch.object(modify, 'remove_activities')
    mocker.patch.object(Person, 'remove_activity')
    person = home_education_shop_education_home

    activities = [False, False, True, True, False]
    modify.remove_selected_activities(person, activities, default='home')

    modify.remove_activities.assert_called_once_with(person, [4, 4], 'home')


@pytest.fixture()
def Steve_Smith_Household():
    Steve = Person(1, attributes={'age': 50, 'job': 'work', 'gender': 'male'})
    Steve.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(5 * 60)))
    Steve.add(Leg(1, 'car', 'a', 'b', start_time=mtdt(5 * 60), end_time=mtdt(6 * 60)))
    Steve.add(Activity(2, 'work', 'b', start_time=mtdt(6 * 60), end_time=mtdt(12 * 60)))
    Steve.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 10)))
    Steve.add(Activity(3, 'leisure', 'c', start_time=mtdt(12 * 60 + 10), end_time=mtdt(13 * 60 - 10)))
    Steve.add(Leg(3, 'walk', 'c', 'b', start_time=mtdt(13 * 60 - 10), end_time=mtdt(13 * 60)))
    Steve.add(Activity(4, 'work', 'b', start_time=mtdt(13 * 60), end_time=mtdt(18 * 60)))
    Steve.add(Leg(4, 'car', 'b', 'a', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)))
    Steve.add(Activity(5, 'home', 'a', start_time=mtdt(19 * 60), end_time=mtdt(24 * 60 - 1)))
    return Steve


@pytest.fixture()
def Hilda_Smith_Household():
    Hilda = Person(2, attributes={'age': 45, 'job': 'influencer', 'gender': 'female'})
    Hilda.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 5)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(8 * 60 + 5), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Leg(1, 'pt', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, 'shop', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(14 * 60)))
    Hilda.add(Leg(2, 'pt', 'b', 'c', start_time=mtdt(14 * 60), end_time=mtdt(14 * 60 + 20)))
    Hilda.add(Activity(3, 'leisure', 'c', start_time=mtdt(14 * 60 + 20), end_time=mtdt(16 * 60 - 20)))
    Hilda.add(Leg(3, 'pt', 'c', 'b', start_time=mtdt(16 * 60 - 20), end_time=mtdt(16 * 60)))
    Hilda.add(Activity(2, 'escort', 'b', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(16 * 60 + 30), end_time=mtdt(16 * 60 + 5)))
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 5), end_time=mtdt(24 * 60 - 1)))
    return Hilda


@pytest.fixture()
def Timmy_Smith_Household():
    Timmy = Person(3, attributes={'age': 18, 'job': 'education', 'gender': 'male'})
    Timmy.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(10 * 60)))
    Timmy.add(Leg(1, 'bike', 'a', 'b', start_time=mtdt(10 * 60), end_time=mtdt(11 * 60)))
    Timmy.add(Activity(2, 'education', 'b', start_time=mtdt(11 * 60), end_time=mtdt(13 * 60)))
    Timmy.add(Leg(2, 'bike', 'b', 'c', start_time=mtdt(13 * 60), end_time=mtdt(13 * 60 + 5)))
    Timmy.add(Activity(3, 'shop', 'c', start_time=mtdt(13 * 60 + 5), end_time=mtdt(13 * 60 + 30)))
    Timmy.add(Leg(3, 'bike', 'c', 'b', start_time=mtdt(13 * 60 + 30), end_time=mtdt(13 * 60 + 35)))
    Timmy.add(Activity(4, 'education', 'b', start_time=mtdt(13 * 60 + 35), end_time=mtdt(15 * 60)))
    Timmy.add(Leg(4, 'bike', 'b', 'd', start_time=mtdt(15 * 60), end_time=mtdt(15 * 60 + 10)))
    Timmy.add(Activity(5, 'leisure', 'd', start_time=mtdt(15 * 60 + 10), end_time=mtdt(18 * 60)))
    Timmy.add(Leg(5, 'bike', 'd', 'a', start_time=mtdt(18 * 60), end_time=mtdt(18 * 60 + 20)))
    Timmy.add(Activity(6, 'home', 'a', start_time=mtdt(18 * 60 + 20), end_time=mtdt(24 * 60 - 1)))
    return Timmy


@pytest.fixture()
def Bobby_Smith_Household():
    Bobby = Person(4, attributes={'age': 6, 'job': 'education', 'gender': 'non-binary'})
    Bobby.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Bobby.add(Leg(1, 'walk', 'a', 'b', start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Bobby.add(Activity(2, 'education', 'b', start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60)))
    Bobby.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(16 * 60), end_time=mtdt(16 * 60 + 30)))
    Bobby.add(Activity(5, 'home', 'a', start_time=mtdt(18 * 60 + 30), end_time=mtdt(24 * 60 - 1)))
    return Bobby


@pytest.fixture()
def Smith_Household(Steve_Smith_Household, Hilda_Smith_Household, Timmy_Smith_Household, Bobby_Smith_Household):
    household = Household(1)
    household.add(Steve_Smith_Household)
    household.add(Hilda_Smith_Household)
    household.add(Timmy_Smith_Household)
    household.add(Bobby_Smith_Household)
    return household


def test_RemoveActivity_apply_to_delegates_policy_type_household_to_evaluate_household_policy(mocker):
    mocker.patch.object(modify.RemoveActivity, 'evaluate_household_policy')
    policy = modify.RemoveActivity(
        ['work'],
        policy_type='household',
        probability=0.5)

    policy.apply_to(Household(1))
    modify.RemoveActivity.evaluate_household_policy.assert_called_once()


def test_RemoveActivity_apply_to_delegates_policy_type_person_to_evaluate_person_policy(mocker):
    mocker.patch.object(modify.RemoveActivity, 'evaluate_person_policy')
    policy = modify.RemoveActivity(
        ['work'],
        policy_type='person',
        probability=0.5)

    policy.apply_to(Household(1))
    modify.RemoveActivity.evaluate_person_policy.assert_called_once()


def test_RemoveActivity_apply_to_delegates_policy_type_activity_to_evaluate_activity_policy(mocker):
    mocker.patch.object(modify.RemoveActivity, 'evaluate_activity_policy')
    policy = modify.RemoveActivity(
        ['work'],
        policy_type='activity',
        probability=0.5)

    policy.apply_to(Household(1))
    modify.RemoveActivity.evaluate_activity_policy.assert_called_once()


def test_evaluate_activity_policy_selects_steve_for_individual_activity_removal(mocker, Smith_Household):
    mocker.patch.object(random, 'random', side_effect=[0] + [1 for i in range(11)])
    household = Smith_Household

    # i.e. First of Steve's work activities is affected and only that activity is affected
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='activity',
        probability_level='activity',
        probability=0.5)
    steve = household.people['1']
    hilda = household.people['2']
    timmy = household.people['3']
    bobby = household.people['4']
    policy.apply_to(household)

    assert len(steve.plan) == 7
    for i in range(0, 7, 2):
        assert isinstance(hilda.plan.day[i], Activity)
    assert [steve.plan.day[i].act for i in range(0, 7, 2)] == ['home', 'leisure', 'work', 'home']

    assert len(hilda.plan) == 11
    for i in range(0, 11, 2):
        assert isinstance(hilda.plan.day[i], Activity)
    assert [hilda.plan.day[i].act for i in range(0, 11, 2)] == ['home', 'escort', 'shop', 'leisure', 'escort', 'home']

    assert len(timmy.plan) == 11
    for i in range(0, 11, 2):
        assert isinstance(timmy.plan.day[i], Activity)
    assert [timmy.plan.day[i].act for i in range(0, 11, 2)] == \
           ['home', 'education', 'shop', 'education', 'leisure', 'home']

    assert len(bobby.plan) == 5
    for i in range(0, 5, 2):
        assert isinstance(bobby.plan.day[i], Activity)
    assert [bobby.plan.day[i].act for i in range(0, 5, 2)] == ['home', 'education', 'home']


def test_household_policy_with_household_based_probability(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[0])
    household = Smith_Household
    # i.e. household is affected and affects activities on household level
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='household',
        probability=0.5)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_household_based_probability_with_a_satisfied_person_attribute(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[0])
    household = Smith_Household
    # i.e. household is affected and affects activities on household level
    def age_condition_under_10(attribute_value):
        return attribute_value < 10
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='household',
        probability=0.5,
        attribute_conditions={'age': age_condition_under_10},
        attribute_strict_conditions=True)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_person_based_probability(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[1, 1, 1, 0])
    household = Smith_Household
    # i.e. Bobby is affected and affects activities on household level
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='person',
        probability=0.5)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_person_based_probability_with_a_satisfied_person_attribute(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[0])
    household = Smith_Household
    # i.e. Bobby is affected and affects activities on household level
    def age_condition_under_10(attribute_value):
        return attribute_value < 10
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='person',
        probability=0.5,
        attribute_conditions={'age': age_condition_under_10},
        attribute_strict_conditions=True)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_activity_based_probability(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[1 for i in range(11)] + [0])
    household = Smith_Household
    # i.e. Bobby's education activity is affected and affects activities on household level
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='activity',
        probability=0.5)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_activity_based_probability_with_a_satisfied_person_attribute(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_household_activities')
    mocker.patch.object(random, 'random', side_effect=[0])
    household = Smith_Household
    # i.e. Bobby's education activity is affected and affects activities on household level
    def age_condition_under_10(attribute_value):
        return attribute_value < 10
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='household',
        probability_level='activity',
        probability=0.5,
        attribute_conditions={'age': age_condition_under_10},
        attribute_strict_conditions=True)
    policy.apply_to(household)

    modify.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_person_policy_with_person_based_probability(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')
    mocker.patch.object(random, 'random', side_effect=[1, 1, 1, 0])
    household = Smith_Household
    # i.e. Bobby is affected and his activities are the only one affected in household
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='person',
        probability_level='person',
        probability=0.5)
    bobby = household.people['4']
    policy.apply_to(household)

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(bobby)


def test_person_policy_with_person_based_probability_with_a_satisfied_person_attribute(mocker, Smith_Household):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')
    mocker.patch.object(random, 'random', side_effect=[1, 1, 1, 0])
    household = Smith_Household
    # i.e. Bobby is affected and his activities are the only one affected in household
    def age_condition_under_10(attribute_value):
        return attribute_value < 10
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='person',
        probability_level='person',
        probability=0.5,
        attribute_conditions={'age': age_condition_under_10},
        attribute_strict_conditions=True)
    bobby = household.people['4']
    policy.apply_to(household)

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(bobby)


def test_person_policy_with_activity_based_probability(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')
    mocker.patch.object(random, 'random', side_effect=[0] + [1 for i in range(11)])
    household = Smith_Household
    # i.e. First of Steve's work activities is affected and affects all listed activities for just Steve
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='person',
        probability_level='activity',
        probability=0.5)
    policy.apply_to(household)
    steve = household.people['1']

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(steve)


def test_person_policy_with_activity_based_probability_with_a_satisfied_person_attribute(Smith_Household, mocker):
    mocker.patch.object(modify.RemoveActivity, 'remove_person_activities')
    mocker.patch.object(random, 'random', side_effect=[0] + [1 for i in range(11)])
    household = Smith_Household
    # i.e. First of Steve's work activities is affected and affects all listed activities for just Steve
    def age_condition_over_20(attribute_value):
        return attribute_value > 20
    policy = modify.RemoveActivity(
        ['education', 'escort', 'leisure', 'shop', 'work'],
        policy_type='person',
        probability_level='activity',
        probability=0.5,
        attribute_conditions={'age': age_condition_over_20},
        attribute_strict_conditions=True)
    policy.apply_to(household)
    steve = household.people['1']

    modify.RemoveActivity.remove_person_activities.assert_called_once_with(steve)

