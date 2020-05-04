from pam.core import Population, Household, Person
from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import modify

import pytest
import random
from datetime import datetime


@pytest.fixture()
def Steve():
    Steve = Person('Steve', attributes={'age': 50, 'job': 'work', 'gender': 'male'})
    Steve.add(Activity(1, 'home', 'a', start_time=mtdt(0), end_time=mtdt(5 * 60)))
    Steve.add(Leg(1, 'car', 'a', 'b', start_time=mtdt(5 * 60), end_time=mtdt(6 * 60)))
    Steve.add(Activity(2, 'work', 'b', start_time=mtdt(6 * 60), end_time=mtdt(12 * 60)))
    Steve.add(Leg(2, 'walk', 'b', 'c', start_time=mtdt(12 * 60), end_time=mtdt(12 * 60 + 10)))
    Steve.add(Activity(3, 'leisure', 'c', start_time=mtdt(12 * 60 + 10), end_time=mtdt(13 * 60 - 10)))
    Steve.add(Leg(3, 'walk', 'c', 'b', start_time=mtdt(13 * 60 - 10), end_time=mtdt(13 * 60)))
    Steve.add(Activity(4, 'work', 'b', start_time=mtdt(13 * 60), end_time=mtdt(18 * 60)))
    Steve.add(Leg(4, 'car', 'b', 'a', start_time=mtdt(18 * 60), end_time=mtdt(19 * 60)))
    Steve.add(Activity(5, 'home', 'a', start_time=mtdt(19 * 60), end_time=END_OF_DAY))
    return Steve


@pytest.fixture()
def Hilda():
    Hilda = Person('Hilda', attributes={'age': 45, 'job': 'influencer', 'gender': 'female'})
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
    Hilda.add(Activity(5, 'home', 'a', start_time=mtdt(16 * 60 + 5), end_time=END_OF_DAY))
    return Hilda


def instantiate_household_with(persons: list):
    household = Household(1)
    for person in persons:
        household.add(person)
    return household


@pytest.fixture()
def Smith_Household(Steve, Hilda):
    return instantiate_household_with([Steve, Hilda])


def test_SamplingProbability_samples_when_random_below_prob_val(mocker):
    mocker.patch.object(modify.SamplingProbability, 'p', return_value=0.55)
    mocker.patch.object(random, 'random', return_value=0.5)
    prob = modify.SamplingProbability()
    assert prob.sample('')


def test_SamplingProbability_doesnt_sample_when_random_above_prob_val(mocker):
    mocker.patch.object(modify.SamplingProbability, 'p', return_value=0.55)
    mocker.patch.object(random, 'random', return_value=0.65)
    prob = modify.SamplingProbability()
    assert not prob.sample('')


def test_SamplingProbability_throws_exception_when_used_for_extracting_p():
    prob = modify.SamplingProbability()
    with pytest.raises(NotImplementedError) as e:
        prob.p('')
    assert 'is a base class' \
           in str(e.value)


def test_SimpleProbability_p_always_returns_same_level_p():
    prob = modify.SimpleProbability(0.45)
    assert prob.p('alfjhlfhlwkhf') == 0.45
    assert prob.p(None) == 0.45
    assert prob.p(modify.Household(1)) == 0.45
    assert prob.p(modify.Person(1)) == 0.45
    assert prob.p(modify.Activity(1)) == 0.45


#### HouseholdProbability


def test_HouseholdProbability_accepts_integer():
    modify.HouseholdProbability(1)


def test_HouseholdProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        modify.HouseholdProbability(2)


def test_HouseholdProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    prob = modify.HouseholdProbability(custom_sampler, {'kwarg': 'kwarg'})
    assert prob.kwargs == {'kwarg': 'kwarg'}


def test_HouseholdProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = modify.HouseholdProbability(custom_sampler)
    assert prob.kwargs == {}
    custom_sampler('', **prob.kwargs)


def test_HouseholdProbability_p_delegates_to_compute_probability_for_household_for_Household(mocker):
    mocker.patch.object(modify.HouseholdProbability, 'compute_probability_for_household', return_value=None)
    prob = modify.HouseholdProbability(0.5)
    hhld = Household(1)
    prob.p(hhld)

    modify.HouseholdProbability.compute_probability_for_household.assert_called_once_with(hhld)


def test_HouseholdProbability_p_throws_exception_when_given_Person():
    prob = modify.HouseholdProbability(0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(Person(1))


def test_HouseholdProbability_p_throws_exception_when_given_Activity():
    prob = modify.HouseholdProbability(0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(Activity(1))


def test_HouseholdProbability_p_throws_exception_when_given_whatever():
    prob = modify.HouseholdProbability(0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(None)


def test_HouseholdProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = modify.HouseholdProbability(0.5)
    assert prob.compute_probability_for_household(Household(1)) == 0.5


def test_HouseholdProbability_compute_probability_for_household_delegates_p_to_custom_callable(mocker):
    called = None
    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = modify.HouseholdProbability(custom_sampler, {'kwarg': 'kwarg'})
    hhld = Household(1)
    assert prob.compute_probability_for_household(hhld) == 0.5
    assert called


#### PersonProbability


def test_PersonProbability_accepts_integer():
    modify.PersonProbability(1)


def test_PersonProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        modify.PersonProbability(2)


def test_PersonProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    prob = modify.PersonProbability(custom_sampler, {'kwarg': 'kwarg'})
    assert prob.kwargs == {'kwarg': 'kwarg'}


def test_PersonProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = modify.PersonProbability(custom_sampler)
    assert prob.kwargs == {}
    custom_sampler('', **prob.kwargs)


def test_PersonProbability_p_delegates_to_compute_probability_for_person_for_each_person_in_Household(
        mocker, Smith_Household):
    mocker.patch.object(modify.PersonProbability, 'compute_probability_for_person', return_value=0.25)
    prob = modify.PersonProbability(0.25)
    p = prob.p(Smith_Household)

    assert modify.PersonProbability.compute_probability_for_person.call_count == 2
    assert p == 0.4375


def test_PersonProbability_p_delegates_to_compute_probability_for_person_for_Person(mocker):
    mocker.patch.object(modify.PersonProbability, 'compute_probability_for_person', return_value=None)
    prob = modify.PersonProbability(0.5)
    person = Person(1)
    prob.p(person)

    modify.PersonProbability.compute_probability_for_person.assert_called_once_with(person)


def test_PersonProbability_p_throws_exception_when_given_Activity():
    prob = modify.PersonProbability(0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(Activity(1))


def test_PersonProbability_p_throws_exception_when_given_whatever():
    prob = modify.PersonProbability(0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(None)


def test_PersonProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = modify.PersonProbability(0.5)
    assert prob.compute_probability_for_person(Person(1)) == 0.5


def test_PersonProbability_compute_probability_for_person_delegates_p_to_custom_callable(mocker):
    called = None

    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = modify.PersonProbability(custom_sampler, {'kwarg': 'kwarg'})
    person = Person(1)
    assert prob.compute_probability_for_person(person) == 0.5
    assert called


#### ActivityProbability


def test_ActivityProbability_accepts_integer():
    modify.ActivityProbability([''], 1)


def test_ActivityProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        modify.ActivityProbability([''], 2)


def test_ActivityProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    prob = modify.ActivityProbability([''], custom_sampler, {'kwarg': 'kwarg'})
    assert prob.kwargs == {'kwarg': 'kwarg'}


def test_ActivityProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = modify.ActivityProbability([''], custom_sampler)
    assert prob.kwargs == {}
    custom_sampler('', **prob.kwargs)


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_each_activity_for_person_in_Household(mocker, Smith_Household):
    mocker.patch.object(modify.ActivityProbability, 'compute_probability_for_activity', return_value=0.25)
    prob = modify.ActivityProbability(['work', 'escort'], 0.25)
    p = prob.p(Smith_Household)

    assert modify.ActivityProbability.compute_probability_for_activity.call_count == 4
    assert p == 0.68359375


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_each_Activity_for_Person(mocker, Steve):
    mocker.patch.object(modify.ActivityProbability, 'compute_probability_for_activity', return_value=0.25)
    prob = modify.ActivityProbability(['work', 'escort'], 0.25)
    person = Steve
    p = prob.p(person)

    assert modify.ActivityProbability.compute_probability_for_activity.call_count == 2
    assert p == 0.4375


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_relevant_Activity(mocker, Steve):
    mocker.patch.object(modify.ActivityProbability, 'compute_probability_for_activity', return_value=0.25)
    prob = modify.ActivityProbability(['work'], 0.25)
    act = [act for act in Steve.activities][1]
    p = prob.p(act)

    modify.ActivityProbability.compute_probability_for_activity.assert_called_once_with(act)
    assert p == 0.25


def test_ActivityProbability_p_returns_0_for_activity_for_irrelevant_Activity(mocker, Steve):
    prob = modify.ActivityProbability(['work'], 0.25)
    act = [act for act in Steve.activities][2]
    p = prob.p(act)

    assert p == 0


def test_ActivityProbability_p_throws_exception_when_given_whatever():
    prob = modify.ActivityProbability([''], 0.5)
    with pytest.raises(NotImplementedError) as e:
        prob.p(None)


def test_ActivityProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = modify.ActivityProbability([''], 0.5)
    assert prob.compute_probability_for_activity(Activity(1)) == 0.5


def test_ActivityProbability_compute_probability_for_activity_delegates_p_to_custom_callable():
    called = None

    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = modify.ActivityProbability([''], custom_sampler, {'kwarg': 'kwarg'})
    assert prob.compute_probability_for_activity(Activity(1)) == 0.5
    assert called


def test_verify_probability_check_list_of_probabilities():
    p_list = [modify.HouseholdProbability(0.5), modify.ActivityProbability([''], 0.5),
              modify.SimpleProbability(0.5), 0.2]
    verified_p_list = modify.verify_probability(
        p_list,
        (float, list, modify.HouseholdProbability, modify.ActivityProbability, modify.SimpleProbability))

    assert p_list[:-1] == verified_p_list[:-1]
    assert isinstance(verified_p_list[-1], modify.SimpleProbability)
    assert verified_p_list[-1].p(None) == 0.2


def test_verify_probability_defaults_acceptable_int_to_simple_probability(mocker):
    mocker.patch.object(modify.SimpleProbability, '__init__', return_value=None)
    modify.verify_probability(1, float)

    modify.SimpleProbability.__init__.assert_called_once_with(1.)


def test_verify_probability_defaults_float_to_simple_probability(mocker):
    mocker.patch.object(modify.SimpleProbability, '__init__', return_value=None)
    modify.verify_probability(0.5, float)

    modify.SimpleProbability.__init__.assert_called_once_with(0.5)


def test_verify_probability_defaults_float_in_list_to_simple_probability(mocker):
    mocker.patch.object(modify.SimpleProbability, '__init__', return_value=None)
    modify.verify_probability([0.3, modify.PersonProbability(0.01)], (float, list, modify.PersonProbability))

    modify.SimpleProbability.__init__.assert_called_once_with(0.3)


# def test_HouseholdPolicy_fails_on_non_probability_value():
#     with pytest.raises(AssertionError) as error_info:
#         modify.verify_probability(1.5, float)
#         print(error_info)
#     print('')
#     assert "p0 and p1 can not be antipodal" in str(error_info.value)


