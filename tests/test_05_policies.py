import random

import pytest
from pam.activity import Activity, Leg
from pam.core import Person
from pam.policy import filters, modifiers, policies, probability_samplers
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def assert_correct_activities_locations(person, ordered_activities_locations_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.location.area for a in person.plan.activities] == ordered_activities_locations_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan) - 1].end_time == END_OF_DAY


@pytest.fixture()
def dummy_modifier():
    class MyModifier(modifiers.Modifier):
        def __init__(self):
            super().__init__()

        def apply_to(self, *args, **kwargs):
            super().apply_to(*args, **kwargs)

    return MyModifier()


def test_subclass_name_features_in_repr_string(dummy_modifier):
    policy = policies.HouseholdPolicy(dummy_modifier, 0.1)
    assert "{}".format(policy.__class__.__name__) in policy.__repr__()


def test_subclass_name_features_in_str_string(dummy_modifier):
    policy = policies.HouseholdPolicy(dummy_modifier, 0.1)
    assert "{}".format(policy.__class__.__name__) in policy.__str__()


@pytest.fixture
def person_home_education_home():
    person = Person(1)
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=END_OF_DAY))

    return person


@pytest.fixture
def home_education_home_education_home():
    person = Person(1)
    person.add(Activity(1, "home", "a"))
    person.add(Leg(1, "car", "a", "b"))
    person.add(Activity(2, "education", "b"))
    person.add(Leg(2, "car", "b", "a"))
    person.add(Activity(3, "home", "a"))
    person.add(Leg(1, "car", "a", "b"))
    person.add(Activity(2, "education", "b"))
    person.add(Leg(2, "car", "b", "a"))
    person.add(Activity(3, "home", "a"))

    return person


@pytest.fixture
def home_education_home_work_home():
    person = Person(1)
    person.add(Activity(1, "home", "a"))
    person.add(Leg(1, "car", "a", "b"))
    person.add(Activity(2, "education", "b"))
    person.add(Leg(2, "car", "b", "a"))
    person.add(Activity(3, "home", "a"))
    person.add(Leg(1, "car", "a", "b"))
    person.add(Activity(2, "work", "d"))
    person.add(Leg(2, "car", "b", "a"))
    person.add(Activity(3, "home", "a"))

    return person


@pytest.fixture
def home_education_shop_home():
    person = Person(1)
    person.add(Activity(1, "home", "a"))
    person.add(Leg(1, "car", "a", "b"))
    person.add(Activity(2, "education", "b"))
    person.add(Leg(2, "car", "b", "b"))
    person.add(Activity(2, "shop", "b"))
    person.add(Leg(2, "car", "b", "a"))
    person.add(Activity(3, "home", "a"))

    return person


@pytest.fixture
def home_education_home_university_student():
    person = Person(1, attributes={"age": 18, "job": "education"})
    person.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(Leg(1, "bike", "a", "b", start_time=mtdt(60), end_time=mtdt(2 * 60)))
    person.add(Activity(2, "education", "b", start_time=mtdt(2 * 60), end_time=mtdt(3 * 60)))
    person.add(Leg(2, "bike", "b", "a", start_time=mtdt(3 * 60), end_time=mtdt(4 * 60)))
    person.add(Activity(3, "home", "a", start_time=mtdt(4 * 60), end_time=END_OF_DAY))

    return person


@pytest.fixture
def home_education_shop_education_home():
    person = Person(1)
    person.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(Leg(1, "car", "a", "b", start_time=mtdt(60), end_time=mtdt(70)))
    person.add(Activity(2, "education", "b", start_time=mtdt(70), end_time=mtdt(100)))
    person.add(Leg(2, "bike", "b", "c", start_time=mtdt(100), end_time=mtdt(120)))
    person.add(Activity(3, "shop", "c", start_time=mtdt(120), end_time=mtdt(180)))
    person.add(Leg(3, "bike", "c", "b", start_time=mtdt(180), end_time=mtdt(200)))
    person.add(Activity(4, "education", "b", start_time=mtdt(200), end_time=mtdt(300)))
    person.add(Leg(4, "car", "b", "a", start_time=mtdt(300), end_time=mtdt(310)))
    person.add(Activity(5, "home", "a", start_time=mtdt(310), end_time=END_OF_DAY))

    return person


def test_home_education_home_removal_of_education_act(
    instantiate_household_with, assert_correct_activities, person_home_education_home
):
    household = instantiate_household_with([person_home_education_home])
    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(activities=["education"]), 1)
    policy.apply_to(household)
    assert_correct_activities(person=household.people[1], ordered_activities_list=["home"])


def test_home_education_home_education_home_removal_of_education_act(
    instantiate_household_with, assert_correct_activities
):
    person = Person(1)
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=mtdt(300)))
    person.add(
        Leg(
            seq=3,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(300),
            end_time=mtdt(390),
        )
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(390), end_time=mtdt(520)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(520),
            end_time=mtdt(580),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(680), end_time=END_OF_DAY))
    household = instantiate_household_with([person])
    assert_correct_activities(
        person=household.people[1],
        ordered_activities_list=["home", "education", "home", "education", "home"],
    )

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(activities=["education"]), 1)
    policy.apply_to(household)
    assert_correct_activities(person=household.people[1], ordered_activities_list=["home"])


def test_home_work_home_education_home_removal_of_education_act(
    instantiate_household_with, assert_correct_activities
):
    person = Person(1)
    person.add(Activity(seq=1, act="home", area="a", start_time=mtdt(0), end_time=mtdt(60)))
    person.add(
        Leg(seq=1, mode="car", start_area="a", end_area="b", start_time=mtdt(60), end_time=mtdt(90))
    )
    person.add(Activity(seq=2, act="work", area="b", start_time=mtdt(90), end_time=mtdt(120)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(120),
            end_time=mtdt(180),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(180), end_time=mtdt(300)))
    person.add(
        Leg(
            seq=3,
            mode="car",
            start_area="a",
            end_area="b",
            start_time=mtdt(300),
            end_time=mtdt(390),
        )
    )
    person.add(Activity(seq=2, act="education", area="b", start_time=mtdt(390), end_time=mtdt(520)))
    person.add(
        Leg(
            seq=2,
            mode="car",
            start_area="b",
            end_area="a",
            start_time=mtdt(520),
            end_time=mtdt(580),
        )
    )
    person.add(Activity(seq=3, act="home", area="a", start_time=mtdt(680), end_time=END_OF_DAY))
    household = instantiate_household_with([person])
    assert_correct_activities(
        person=household.people[1],
        ordered_activities_list=["home", "work", "home", "education", "home"],
    )

    policy = policies.ActivityPolicy(modifiers.RemoveActivity(activities=["education"]), 1)
    policy.apply_to(household)
    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "work", "home"]
    )


def test_attribute_based_remove_activity_policy_removes_all_matching_activities_from_strictly_relevant_people(
    instantiate_household_with, assert_correct_activities, home_education_home_university_student
):
    household = instantiate_household_with([home_education_home_university_student])

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_education(attribute_value):
        return attribute_value == "education"

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )
    assert age_condition_over_17(household.people[1].attributes["age"])
    assert job_condition_education(household.people[1].attributes["job"])

    policy_remove_higher_education = policies.ActivityPolicy(
        modifiers.RemoveActivity(["education"]),
        probability_samplers.ActivityProbability(["education"], 1),
        filters.PersonAttributeFilter(
            conditions={"age": age_condition_over_17, "job": job_condition_education}, how="all"
        ),
    )

    policy_remove_higher_education.apply_to(household)
    assert_correct_activities(person=household.people[1], ordered_activities_list=["home"])


def test_attribute_based_remove_activity_policy_does_not_remove_matching_activities_from_strictly_irrelevant_people(
    instantiate_household_with, assert_correct_activities, home_education_home_university_student
):
    household = instantiate_household_with([home_education_home_university_student])

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == "wasevrrr"

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )
    assert age_condition_over_17(household.people[1].attributes["age"])
    assert not job_condition_wasevrrr(household.people[1].attributes["job"])

    policy_remove_higher_education = policies.ActivityPolicy(
        modifiers.RemoveActivity(["education"]),
        probability_samplers.ActivityProbability(["education"], 1),
        filters.PersonAttributeFilter(
            conditions={"age": age_condition_over_17, "job": job_condition_wasevrrr}, how="all"
        ),
    )

    policy_remove_higher_education.apply_to(household)

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )


def test_attribute_based_remove_activity_policy_removes_all_matching_activities_from_non_strictly_relevant_people(
    instantiate_household_with, assert_correct_activities, home_education_home_university_student
):
    household = instantiate_household_with([home_education_home_university_student])

    def age_condition_over_17(attribute_value):
        return attribute_value > 17

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == "wasevrrr"

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )
    assert age_condition_over_17(household.people[1].attributes["age"])
    assert not job_condition_wasevrrr(household.people[1].attributes["job"])

    policy_remove_higher_education = policies.ActivityPolicy(
        modifiers.RemoveActivity(["education"]),
        probability_samplers.ActivityProbability(["education"], 1),
        filters.PersonAttributeFilter(
            conditions={"age": age_condition_over_17, "job": job_condition_wasevrrr}, how="any"
        ),
    )

    policy_remove_higher_education.apply_to(household)

    assert_correct_activities(person=household.people[1], ordered_activities_list=["home"])


def test_attribute_based_remove_activity_policy_does_not_remove_matching_activities_from_non_strictly_irrelevant_people(
    instantiate_household_with, assert_correct_activities, home_education_home_university_student
):
    household = instantiate_household_with([home_education_home_university_student])

    def age_condition_under_0(attribute_value):
        return attribute_value < 0

    def job_condition_wasevrrr(attribute_value):
        return attribute_value == "wasevrrr"

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )
    assert not age_condition_under_0(household.people[1].attributes["age"])
    assert not job_condition_wasevrrr(household.people[1].attributes["job"])

    policy_remove_higher_education = policies.ActivityPolicy(
        modifiers.RemoveActivity(["education"]),
        probability_samplers.ActivityProbability(["education"], 1),
        filters.PersonAttributeFilter(
            conditions={"age": age_condition_under_0, "job": job_condition_wasevrrr}, how="any"
        ),
    )

    policy_remove_higher_education.apply_to(household)

    assert_correct_activities(
        person=household.people[1], ordered_activities_list=["home", "education", "home"]
    )


def test_remove_activity_policy_only_removes_individual_activities(
    assert_correct_activities, home_education_shop_education_home
):
    person = home_education_shop_education_home
    assert_correct_activities(
        person=person, ordered_activities_list=["home", "education", "shop", "education", "home"]
    )
    act_to_remove = list(person.activities)[3]

    policy_remove_education = modifiers.RemoveActivity(["education"])
    policy_remove_education.remove_individual_activities(person, [act_to_remove])

    assert_correct_activities(
        person=person, ordered_activities_list=["home", "education", "shop", "home"]
    )


def test_evaluate_activity_policy_selects_steve_for_individual_activity_removal(
    assert_correct_activities, mocker, SmithHousehold
):
    mocker.patch.object(random, "random", side_effect=[1] + [0] + [1] * 18)
    household = SmithHousehold
    steve = household.people[1]
    hilda = household.people[2]
    timmy = household.people[3]
    bobby = household.people[4]

    assert_correct_activities(
        person=steve, ordered_activities_list=["home", "work", "leisure", "work", "home"]
    )
    assert_correct_activities(
        person=hilda,
        ordered_activities_list=[
            "home",
            "escort_education",
            "shop",
            "leisure",
            "escort_education",
            "home",
        ],
    )
    assert_correct_activities(
        person=timmy,
        ordered_activities_list=["home", "education", "shop", "education", "leisure", "home"],
    )
    assert_correct_activities(person=bobby, ordered_activities_list=["home", "education", "home"])

    # i.e. First of Steve's work activities is affected and only that activity is affected
    policy = policies.ActivityPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.ActivityProbability(
            ["education", "escort", "leisure", "shop", "work"], 0.5
        ),
    )
    policy.apply_to(household)

    assert_correct_activities(
        person=steve, ordered_activities_list=["home", "leisure", "work", "home"]
    )
    assert_correct_activities(
        person=hilda,
        ordered_activities_list=[
            "home",
            "escort_education",
            "shop",
            "leisure",
            "escort_education",
            "home",
        ],
    )
    assert_correct_activities(
        person=timmy,
        ordered_activities_list=["home", "education", "shop", "education", "leisure", "home"],
    )
    assert_correct_activities(person=bobby, ordered_activities_list=["home", "education", "home"])


def test_household_policy_with_household_based_probability(SmithHousehold, mocker):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0])
    household = SmithHousehold
    # i.e. household is affected and affects activities on household level
    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.HouseholdProbability(0.5),
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_household_based_probability_with_a_satisfied_person_attribute(
    SmithHousehold, mocker
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0])
    household = SmithHousehold

    # i.e. household is affected and affects activities on household level
    def discrete_sampler(obj, mapping, distribution):
        p = distribution
        for key in mapping:
            value = obj.attributes.get(key)
            if value is None:
                raise KeyError(f"Cannot find mapping: {key} in sampling features: {obj.attributes}")
            p = p.get(value)
            if p is None:
                raise KeyError(f"Cannot find feature for {key}: {value} in distribution: {p}")
        return p

    age_mapping = ["age"]
    below_10 = [i for i in range(11)]
    above_10 = [i for i in range(11, 101)]
    age_distribution = {
        **dict(zip(below_10, [1] * len(below_10))),
        **dict(zip(above_10, [0] * len(above_10))),
    }

    people_satisfying_age_condition_under_10 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_under_10 += discrete_sampler(
            person, age_mapping, age_distribution
        )
    assert people_satisfying_age_condition_under_10 == 1

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        [
            probability_samplers.HouseholdProbability(0.5),
            probability_samplers.PersonProbability(
                discrete_sampler, {"mapping": age_mapping, "distribution": age_distribution}
            ),
        ],
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_person_based_probability(SmithHousehold, mocker):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0.06249])
    household = SmithHousehold
    # i.e. Bobby is affected and affects activities on household level
    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.PersonProbability(0.5),
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_person_based_probability_with_a_satisfied_person_attribute(
    SmithHousehold, mocker
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0])
    household = SmithHousehold

    # i.e. Bobby is affected and affects activities on household level
    def discrete_sampler(obj, mapping, distribution):
        p = distribution
        for key in mapping:
            value = obj.attributes.get(key)
            if value is None:
                raise KeyError(f"Cannot find mapping: {key} in sampling features: {obj.attributes}")
            p = p.get(value)
            if p is None:
                raise KeyError(f"Cannot find feature for {key}: {value} in distribution: {p}")
        return p

    age_mapping = ["age"]
    below_10 = [i for i in range(11)]
    above_10 = [i for i in range(11, 101)]
    age_distribution = {
        **dict(zip(below_10, [1] * len(below_10))),
        **dict(zip(above_10, [0] * len(above_10))),
    }

    people_satisfying_age_condition_under_10 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_under_10 += discrete_sampler(
            person, age_mapping, age_distribution
        )
    assert people_satisfying_age_condition_under_10 == 1

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.PersonProbability(
            discrete_sampler, {"mapping": age_mapping, "distribution": age_distribution}
        ),
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_activity_based_probability(SmithHousehold, mocker):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0.000244140624])
    household = SmithHousehold
    # i.e. Bobby's education activity is affected and affects activities on household level
    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.ActivityProbability(
            ["education", "escort", "leisure", "shop", "work"], 0.5
        ),
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_household_policy_with_activity_based_probability_with_a_satisfied_person_attribute(
    SmithHousehold, mocker
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_household_activities")
    mocker.patch.object(random, "random", side_effect=[0])
    household = SmithHousehold

    # i.e. Bobby's education activity is affected and affects activities on household level
    def discrete_sampler(obj, mapping, distribution):
        p = distribution
        for key in mapping:
            value = obj.attributes.get(key)
            if value is None:
                raise KeyError(f"Cannot find mapping: {key} in sampling features: {obj.attributes}")
            p = p.get(value)
            if p is None:
                raise KeyError(f"Cannot find feature for {key}: {value} in distribution: {p}")
        return p

    age_mapping = ["age"]
    below_10 = [i for i in range(11)]
    above_10 = [i for i in range(11, 101)]
    age_distribution = {
        **dict(zip(below_10, [1] * len(below_10))),
        **dict(zip(above_10, [0] * len(above_10))),
    }

    people_satisfying_age_condition_under_10 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_under_10 += discrete_sampler(
            person, age_mapping, age_distribution
        )
    assert people_satisfying_age_condition_under_10 == 1

    policy = policies.HouseholdPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        [
            probability_samplers.ActivityProbability(
                ["education", "escort", "leisure", "shop", "work"], 0.5
            ),
            probability_samplers.PersonProbability(
                discrete_sampler, {"mapping": age_mapping, "distribution": age_distribution}
            ),
        ],
    )
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_household_activities.assert_called_once_with(household)


def test_person_policy_with_person_based_probability(mocker, SmithHousehold):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")
    mocker.patch.object(random, "random", side_effect=[1, 1, 1, 0])
    household = SmithHousehold
    # i.e. Bobby is affected and his activities are the only one affected in household
    policy = policies.PersonPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.PersonProbability(0.5),
    )
    bobby = household.people[4]
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_person_activities.assert_called_once_with(bobby)


def test_person_policy_with_person_based_probability_with_a_satisfied_person_attribute(
    mocker, SmithHousehold
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")
    mocker.patch.object(random, "random", side_effect=[1, 1, 1, 0])
    household = SmithHousehold

    # i.e. Bobby is affected and his activities are the only one affected in household
    def discrete_sampler(obj, mapping, distribution):
        p = distribution
        for key in mapping:
            value = obj.attributes.get(key)
            if value is None:
                raise KeyError(f"Cannot find mapping: {key} in sampling features: {obj.attributes}")
            p = p.get(value)
            if p is None:
                raise KeyError(f"Cannot find feature for {key}: {value} in distribution: {p}")
        return p

    age_mapping = ["age"]
    below_10 = [i for i in range(11)]
    above_10 = [i for i in range(11, 101)]
    age_distribution = {
        **dict(zip(below_10, [1] * len(below_10))),
        **dict(zip(above_10, [0] * len(above_10))),
    }

    people_satisfying_age_condition_under_10 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_under_10 += discrete_sampler(
            person, age_mapping, age_distribution
        )
    assert people_satisfying_age_condition_under_10 == 1

    policy = policies.PersonPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.PersonProbability(
            discrete_sampler, {"mapping": age_mapping, "distribution": age_distribution}
        ),
    )
    bobby = household.people[4]
    policy.apply_to(household)

    modifiers.RemoveActivity.remove_person_activities.assert_called_once_with(bobby)


def test_person_policy_with_activity_based_probability(SmithHousehold, mocker):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")
    mocker.patch.object(random, "random", side_effect=[0] + [1] * 11)
    household = SmithHousehold
    # i.e. First of Steve's work activities is affected and affects all listed activities for just Steve
    policy = policies.PersonPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        probability_samplers.ActivityProbability(
            ["education", "escort", "leisure", "shop", "work"], 0.5
        ),
    )
    policy.apply_to(household)
    steve = household.people[1]

    modifiers.RemoveActivity.remove_person_activities.assert_called_once_with(steve)


def test_person_policy_with_activity_based_probability_with_a_satisfied_person_attribute(
    SmithHousehold, mocker
):
    mocker.patch.object(modifiers.RemoveActivity, "remove_person_activities")
    mocker.patch.object(random, "random", side_effect=[0] + [1] * 11)
    household = SmithHousehold

    # i.e. First of Steve's work activities is affected and affects all listed activities for just Steve
    def discrete_sampler(obj, mapping, distribution):
        p = distribution
        for key in mapping:
            value = obj.attributes.get(key)
            if value is None:
                raise KeyError(f"Cannot find mapping: {key} in sampling features: {obj.attributes}")
            p = p.get(value)
            if p is None:
                raise KeyError(f"Cannot find feature for {key}: {value} in distribution: {p}")
        return p

    age_mapping = ["age"]
    below_20 = [i for i in range(21)]
    above_20 = [i for i in range(21, 101)]
    age_distribution = {
        **dict(zip(below_20, [0] * len(below_20))),
        **dict(zip(above_20, [1] * len(above_20))),
    }

    people_satisfying_age_condition_over_20 = 0
    for pid, person in household.people.items():
        people_satisfying_age_condition_over_20 += discrete_sampler(
            person, age_mapping, age_distribution
        )
    assert people_satisfying_age_condition_over_20 == 2

    policy = policies.PersonPolicy(
        modifiers.RemoveActivity(["education", "escort", "leisure", "shop", "work"]),
        [
            probability_samplers.ActivityProbability(
                ["education", "escort", "leisure", "shop", "work"], 0.5
            ),
            probability_samplers.PersonProbability(
                discrete_sampler, {"mapping": age_mapping, "distribution": age_distribution}
            ),
        ],
    )
    policy.apply_to(household)
    steve = household.people[1]

    modifiers.RemoveActivity.remove_person_activities.assert_called_once_with(steve)


##### MoveActivityToHomeLocation


def test_MoveActivityToHomeLocation_moves_shop_to_home_location(instantiate_household_with):
    Hilda = Person(1, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "car", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, "car", "b", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    hhld = instantiate_household_with([Hilda])

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(hhld)

    assert Hilda.plan[2].location == Hilda.home
    assert Hilda.plan[2].is_exact(
        Activity(2, "shop", "a", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30))
    )


def test_MoveActivityToHomeLocation_updates_Legs_after_moving_shopping_trip(
    instantiate_household_with,
):
    Hilda = Person(1, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "car", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, "car", "b", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))

    hhld = instantiate_household_with([Hilda])

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(hhld)

    assert Hilda.plan.validate_locations()


def test_MoveActivityToHomeLocation_performs_mode_shift_after_moving_shopping_trip(
    instantiate_household_with,
):
    Hilda = Person(1, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "pt", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, "pt", "b", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    hhld = instantiate_household_with([Hilda])

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(hhld)
    assert Hilda.plan[1].mode != "pt"
    assert Hilda.plan[3].mode != "pt"


def test_MoveActivityToHomeLocation_performs_mode_shift_to_car(instantiate_household_with):
    Hilda = Person(
        1, attributes={"age": 45, "job": "influencer", "gender": "female", "driving_licence": True}
    )
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "pt", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, "pt", "b", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    hhld = instantiate_household_with([Hilda])

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"], new_mode="car"),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(hhld)

    assert Hilda.plan[1].mode == "car"
    assert Hilda.plan[3].mode == "car"


def test_MoveActivityToHomeLocation_performs_mode_shift_to_walk(instantiate_household_with):
    Hilda = Person(
        1, attributes={"age": 45, "job": "influencer", "gender": "female", "driving_licence": False}
    )
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "pt", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(1, "pt", "b", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    hhld = instantiate_household_with([Hilda])

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(hhld)

    assert Hilda.plan[1].mode == "walk"
    assert Hilda.plan[3].mode == "walk"


def test_MoveActivityToHomeLocation_moves_shopping_tour_to_home_location(
    assert_correct_activities, SmithHousehold
):
    household = SmithHousehold
    Steve = household.people[1]
    Timmy = household.people[3]
    Timmy.plan[4].act = "shop_1"
    Bobby = household.people[4]

    Hilda = Person(2, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop_1", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(2, "walk", "b", "c", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(3, "shop_2", "c", start_time=mtdt(8 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(3, "walk", "c", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(4, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    household.people[2] = Hilda

    assert_correct_activities(
        person=Steve, ordered_activities_list=["home", "work", "leisure", "work", "home"]
    )
    assert_correct_activities_locations(
        person=Steve, ordered_activities_locations_list=["a", "b", "c", "b", "a"]
    )
    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop_1", "shop_2", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "b", "c", "a"]
    )
    assert_correct_activities(
        person=Timmy,
        ordered_activities_list=["home", "education", "shop_1", "education", "leisure", "home"],
    )
    assert_correct_activities_locations(
        person=Timmy, ordered_activities_locations_list=["a", "b", "c", "b", "d", "a"]
    )
    assert_correct_activities(person=Bobby, ordered_activities_list=["home", "education", "home"])
    assert_correct_activities_locations(
        person=Bobby, ordered_activities_locations_list=["a", "b", "a"]
    )

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop_1", "shop_2"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(household)

    assert_correct_activities(
        person=Steve, ordered_activities_list=["home", "work", "leisure", "work", "home"]
    )
    assert_correct_activities_locations(
        person=Steve, ordered_activities_locations_list=["a", "b", "c", "b", "a"]
    )
    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop_1", "shop_2", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "a", "a", "a"]
    )
    assert_correct_activities(
        person=Timmy,
        ordered_activities_list=["home", "education", "shop_1", "education", "leisure", "home"],
    )
    assert_correct_activities_locations(
        person=Timmy, ordered_activities_locations_list=["a", "b", "c", "b", "d", "a"]
    )
    assert_correct_activities(person=Bobby, ordered_activities_list=["home", "education", "home"])
    assert_correct_activities_locations(
        person=Bobby, ordered_activities_locations_list=["a", "b", "a"]
    )


def test_MoveActivityToHomeLocation_moves_partial_fit_shopping_tours(
    assert_correct_activities, SmithHousehold
):
    household = SmithHousehold
    Hilda = Person(2, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop_1", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(10 * 60 + 30)))
    Hilda.add(Leg(2, "walk", "a", "a", start_time=mtdt(10 * 60 + 30), end_time=mtdt(11 * 60)))
    Hilda.add(Activity(3, "home", "a", start_time=mtdt(11 * 60), end_time=mtdt(12 * 60)))
    Hilda.add(Leg(3, "walk", "a", "c", start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 30)))
    Hilda.add(
        Activity(4, "shop_2", "c", start_time=mtdt(12 * 60 + 30), end_time=mtdt(16 * 60 + 30))
    )
    Hilda.add(Leg(4, "walk", "c", "a", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "home", "a", start_time=mtdt(17 * 60), end_time=END_OF_DAY))
    household.people[2] = Hilda

    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop_1", "home", "shop_2", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "b", "a", "c", "a"]
    )

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop_1", "shop_2"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(household)

    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop_1", "home", "shop_2", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "a", "a", "a", "a"]
    )


def test_MoveActivityToHomeLocation_does_moves_only_valid_shopping_tour(
    assert_correct_activities, SmithHousehold
):
    household = SmithHousehold
    Hilda = Person(2, attributes={"age": 45, "job": "influencer", "gender": "female"})
    Hilda.add(Activity(1, "home", "a", start_time=mtdt(0), end_time=mtdt(8 * 60)))
    Hilda.add(Leg(1, "walk", "a", "b", start_time=mtdt(8 * 60), end_time=mtdt(8 * 60 + 30)))
    Hilda.add(Activity(2, "shop", "b", start_time=mtdt(8 * 60 + 30), end_time=mtdt(10 * 60 + 30)))
    Hilda.add(Leg(2, "walk", "a", "a", start_time=mtdt(10 * 60 + 30), end_time=mtdt(11 * 60)))
    Hilda.add(Activity(3, "home", "a", start_time=mtdt(11 * 60), end_time=mtdt(12 * 60)))
    Hilda.add(Leg(3, "walk", "a", "c", start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 30)))
    Hilda.add(Activity(4, "shop", "c", start_time=mtdt(12 * 60 + 30), end_time=mtdt(16 * 60 + 30)))
    Hilda.add(Leg(4, "walk", "a", "c", start_time=mtdt(16 * 60 + 30), end_time=mtdt(17 * 60)))
    Hilda.add(Activity(5, "leisure", "c", start_time=mtdt(17 * 60), end_time=mtdt(17 * 60 + 30)))
    Hilda.add(Leg(5, "walk", "c", "a", start_time=mtdt(17 * 60 + 30), end_time=mtdt(18 * 60)))
    Hilda.add(Activity(6, "home", "a", start_time=mtdt(18 * 60), end_time=END_OF_DAY))
    household.people[2] = Hilda

    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop", "home", "shop", "leisure", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "b", "a", "c", "c", "a"]
    )

    policy = policies.PersonPolicy(
        modifiers.MoveActivityTourToHomeLocation(["shop"]),
        probability_samplers.PersonProbability(1),
    )
    policy.apply_to(household)

    assert_correct_activities(
        person=Hilda, ordered_activities_list=["home", "shop", "home", "shop", "leisure", "home"]
    )
    assert_correct_activities_locations(
        person=Hilda, ordered_activities_locations_list=["a", "a", "a", "c", "c", "a"]
    )
