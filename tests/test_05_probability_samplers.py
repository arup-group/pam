import random

import pytest
from pam.activity import Activity
from pam.core import Household, Person
from pam.policy import probability_samplers


@pytest.fixture()
def SmithHousehold_alt(instantiate_household_with, Steve, Hilda):
    return instantiate_household_with([Steve, Hilda])


@pytest.fixture()
def dummy_sampler():
    class MySampler(probability_samplers.SamplingProbability):
        def __init__(self, probability):
            super().__init__(probability)

        def p(self, p):
            return self.probability

    return MySampler(0.55)


def test_SamplingProbability_samples_when_random_below_prob_val(mocker, dummy_sampler):
    mocker.patch.object(random, "random", return_value=0.5)
    assert dummy_sampler.sample("")


def test_SamplingProbability_samples_when_random_equal_prob_val(mocker, dummy_sampler):
    mocker.patch.object(random, "random", return_value=0.55)
    assert not dummy_sampler.sample("")


def test_SamplingProbability_doesnt_sample_when_random_above_prob_val(mocker, dummy_sampler):
    mocker.patch.object(random, "random", return_value=0.65)
    assert not dummy_sampler.sample("")


def test_SimpleProbability_p_always_returns_same_level_p():
    prob = probability_samplers.SimpleProbability(0.45)
    assert prob.p("alfjhlfhlwkhf") == 0.45
    assert prob.p(None) == 0.45
    assert prob.p(Household(1)) == 0.45
    assert prob.p(Person(1)) == 0.45
    assert prob.p(Activity(1)) == 0.45


#### HouseholdProbability


def test_HouseholdProbability_accepts_integer():
    probability_samplers.HouseholdProbability(1)


def test_HouseholdProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        probability_samplers.HouseholdProbability(2)


def test_HouseholdProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    assert callable(custom_sampler)
    prob = probability_samplers.HouseholdProbability(custom_sampler, {"kwarg": "kwarg"})
    assert prob.kwargs == {"kwarg": "kwarg"}


def test_HouseholdProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = probability_samplers.HouseholdProbability(custom_sampler)
    assert prob.kwargs == {}
    custom_sampler("", **prob.kwargs)


def test_HouseholdProbability_p_delegates_to_compute_probability_for_household_for_Household(
    mocker,
):
    mocker.patch.object(
        probability_samplers.HouseholdProbability,
        "compute_probability_for_household",
        return_value=None,
    )
    prob = probability_samplers.HouseholdProbability(0.5)
    hhld = Household(1)
    prob.p(hhld)

    probability_samplers.HouseholdProbability.compute_probability_for_household.assert_called_once_with(
        hhld
    )


def test_HouseholdProbability_p_throws_exception_when_given_Person():
    prob = probability_samplers.HouseholdProbability(0.5)
    with pytest.raises(NotImplementedError):
        prob.p(Person(1))


def test_HouseholdProbability_p_throws_exception_when_given_Activity():
    prob = probability_samplers.HouseholdProbability(0.5)
    with pytest.raises(NotImplementedError):
        prob.p(Activity(1))


def test_HouseholdProbability_p_throws_exception_when_given_whatever():
    prob = probability_samplers.HouseholdProbability(0.5)
    with pytest.raises(TypeError):
        prob.p(None)


def test_HouseholdProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = probability_samplers.HouseholdProbability(0.5)
    assert prob.compute_probability_for_household(Household(1)) == 0.5


def test_HouseholdProbability_compute_probability_for_household_delegates_p_to_custom_callable(
    mocker,
):
    called = None

    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = probability_samplers.HouseholdProbability(custom_sampler, {"kwarg": "kwarg"})
    hhld = Household(1)
    assert prob.compute_probability_for_household(hhld) == 0.5
    assert called


#### PersonProbability


def test_PersonProbability_accepts_integer():
    probability_samplers.PersonProbability(1)


def test_PersonProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        probability_samplers.PersonProbability(2)


def test_PersonProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    prob = probability_samplers.PersonProbability(custom_sampler, {"kwarg": "kwarg"})
    assert prob.kwargs == {"kwarg": "kwarg"}


def test_PersonProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = probability_samplers.PersonProbability(custom_sampler)
    assert prob.kwargs == {}
    custom_sampler("", **prob.kwargs)


def test_PersonProbability_p_delegates_to_compute_probability_for_person_for_each_person_in_Household(
    mocker, SmithHousehold_alt
):
    mocker.patch.object(
        probability_samplers.PersonProbability, "compute_probability_for_person", return_value=0.25
    )
    prob = probability_samplers.PersonProbability(0.25)
    p = prob.p(SmithHousehold_alt)

    assert probability_samplers.PersonProbability.compute_probability_for_person.call_count == 2
    assert p == 0.4375


def test_PersonProbability_p_delegates_to_compute_probability_for_person_for_Person(mocker):
    mocker.patch.object(
        probability_samplers.PersonProbability, "compute_probability_for_person", return_value=None
    )
    prob = probability_samplers.PersonProbability(0.5)
    person = Person(1)
    prob.p(person)

    probability_samplers.PersonProbability.compute_probability_for_person.assert_called_once_with(
        person
    )


def test_PersonProbability_p_throws_exception_when_given_Activity():
    prob = probability_samplers.PersonProbability(0.5)
    with pytest.raises(NotImplementedError):
        prob.p(Activity(1))


def test_PersonProbability_p_throws_exception_when_given_whatever():
    prob = probability_samplers.PersonProbability(0.5)
    with pytest.raises(NotImplementedError):
        prob.p(None)


def test_PersonProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = probability_samplers.PersonProbability(0.5)
    assert prob.compute_probability_for_person(Person(1)) == 0.5


def test_PersonProbability_compute_probability_for_person_delegates_p_to_custom_callable(mocker):
    called = None

    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = probability_samplers.PersonProbability(custom_sampler, {"kwarg": "kwarg"})
    person = Person(1)
    assert prob.compute_probability_for_person(person) == 0.5
    assert called


#### ActivityProbability


def test_ActivityProbability_accepts_integer():
    probability_samplers.ActivityProbability([""], 1)


def test_ActivityProbability_fails_non_probability_integers():
    with pytest.raises(AssertionError):
        probability_samplers.ActivityProbability([""], 2)


def test_ActivityProbability_accepts_functions():
    def custom_sampler(x, kwarg):
        return 0.5

    prob = probability_samplers.ActivityProbability([""], custom_sampler, {"kwarg": "kwarg"})
    assert prob.kwargs == {"kwarg": "kwarg"}


def test_ActivityProbability_defaults_to_empty_kwargs_with_custom_distros():
    def custom_sampler(x):
        return 0.5

    prob = probability_samplers.ActivityProbability([""], custom_sampler)
    assert prob.kwargs == {}
    custom_sampler("", **prob.kwargs)


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_each_activity_for_person_in_Household(
    mocker, SmithHousehold_alt
):
    mocker.patch.object(
        probability_samplers.ActivityProbability,
        "compute_probability_for_activity",
        return_value=0.25,
    )
    prob = probability_samplers.ActivityProbability(["work", "escort_education"], 0.25)
    p = prob.p(SmithHousehold_alt)

    assert probability_samplers.ActivityProbability.compute_probability_for_activity.call_count == 4
    assert p == 0.68359375


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_each_Activity_for_Person(
    mocker, Steve
):
    mocker.patch.object(
        probability_samplers.ActivityProbability,
        "compute_probability_for_activity",
        return_value=0.25,
    )
    prob = probability_samplers.ActivityProbability(["work", "escort"], 0.25)
    person = Steve
    p = prob.p(person)

    assert probability_samplers.ActivityProbability.compute_probability_for_activity.call_count == 2
    assert p == 0.4375


def test_ActivityProbability_p_delegates_to_compute_probability_for_activity_for_relevant_Activity(
    mocker, Steve
):
    mocker.patch.object(
        probability_samplers.ActivityProbability,
        "compute_probability_for_activity",
        return_value=0.25,
    )
    prob = probability_samplers.ActivityProbability(["work"], 0.25)
    act = [act for act in Steve.activities][1]
    p = prob.p(act)

    probability_samplers.ActivityProbability.compute_probability_for_activity.assert_called_once_with(
        act
    )
    assert p == 0.25


def test_ActivityProbability_p_returns_0_for_activity_for_irrelevant_Activity(mocker, Steve):
    prob = probability_samplers.ActivityProbability(["work"], 0.25)
    act = [act for act in Steve.activities][2]
    p = prob.p(act)

    assert p == 0


def test_ActivityProbability_p_throws_exception_when_given_whatever():
    prob = probability_samplers.ActivityProbability([""], 0.5)
    with pytest.raises(NotImplementedError):
        prob.p(None)


def test_ActivityProbability_compute_probability_for_household_returns_same_level_p_for_floats():
    prob = probability_samplers.ActivityProbability([""], 0.5)
    assert prob.compute_probability_for_activity(Activity(1)) == 0.5


def test_ActivityProbability_compute_probability_for_activity_delegates_p_to_custom_callable():
    called = None

    def custom_sampler(x, kwarg):
        nonlocal called
        called = True
        return 0.5

    prob = probability_samplers.ActivityProbability([""], custom_sampler, {"kwarg": "kwarg"})
    assert prob.compute_probability_for_activity(Activity(1)) == 0.5
    assert called


def test_verify_probability_check_list_of_probabilities():
    p_list = [
        probability_samplers.HouseholdProbability(0.5),
        probability_samplers.ActivityProbability([""], 0.5),
        probability_samplers.SimpleProbability(0.5),
        0.2,
    ]
    verified_p_list = probability_samplers.verify_probability(p_list)

    assert p_list[:-1] == verified_p_list[:-1]
    assert isinstance(verified_p_list[-1], probability_samplers.SimpleProbability)
    assert verified_p_list[-1].p(None) == 0.2


def test_verify_probability_defaults_acceptable_int_to_simple_probability(mocker):
    mocker.patch.object(probability_samplers.SimpleProbability, "__init__", return_value=None)
    probability_samplers.verify_probability(1)

    probability_samplers.SimpleProbability.__init__.assert_called_once_with(1.0)


def test_verify_probability_defaults_float_to_simple_probability(mocker):
    mocker.patch.object(probability_samplers.SimpleProbability, "__init__", return_value=None)
    probability_samplers.verify_probability(0.5)

    probability_samplers.SimpleProbability.__init__.assert_called_once_with(0.5)


def test_verify_probability_defaults_float_in_list_to_simple_probability(mocker):
    mocker.patch.object(probability_samplers.SimpleProbability, "__init__", return_value=None)
    probability_samplers.verify_probability([0.3, probability_samplers.PersonProbability(0.01)])

    probability_samplers.SimpleProbability.__init__.assert_called_once_with(0.3)
