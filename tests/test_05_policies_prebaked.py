import pam.policy.modifiers as modifiers
import pam.policy.probability_samplers as probability_samplers
from pam.policy.policies import (
    ActivityPolicy,
    HouseholdPolicy,
    MovePersonActivitiesToHome,
    PersonPolicy,
    ReduceSharedHouseholdActivities,
    RemoveHouseholdActivities,
    RemoveIndividualActivities,
    RemovePersonActivities,
)


def test_RemoveHouseholdActivities_initiates_correct_policy():
    policy = RemoveHouseholdActivities(["activity"], 0.5)

    assert isinstance(policy, HouseholdPolicy)
    assert isinstance(policy.modifier, modifiers.RemoveActivity)
    assert policy.modifier.activities == ["activity"]
    assert isinstance(policy.probability, probability_samplers.SimpleProbability)


def test_RemovePersonActivities_initiates_correct_policy():
    policy = RemovePersonActivities(["activity"], 0.5)

    assert isinstance(policy, PersonPolicy)
    assert isinstance(policy.modifier, modifiers.RemoveActivity)
    assert policy.modifier.activities == ["activity"]
    assert isinstance(policy.probability, probability_samplers.SimpleProbability)


def test_RemoveIndividualActivities_initiates_correct_policy():
    policy = RemoveIndividualActivities(["activity"], 0.5)

    assert isinstance(policy, ActivityPolicy)
    assert isinstance(policy.modifier, modifiers.RemoveActivity)
    assert policy.modifier.activities == ["activity"]
    assert isinstance(policy.probability, probability_samplers.SimpleProbability)


def test_MovePersonActivitiesToHome_initiates_correct_policy():
    policy = MovePersonActivitiesToHome(["activity"], 0.5)

    assert isinstance(policy, PersonPolicy)
    assert isinstance(policy.modifier, modifiers.MoveActivityTourToHomeLocation)
    assert policy.modifier.activities == ["activity"]
    assert isinstance(policy.probability, probability_samplers.SimpleProbability)


def test_ReduceSharedHouseholdActivities_initiates_correct_policy():
    policy = ReduceSharedHouseholdActivities(["activity"], 0.5)

    assert isinstance(policy, HouseholdPolicy)
    assert isinstance(policy.modifier, modifiers.ReduceSharedActivity)
    assert policy.modifier.activities == ["activity"]
    assert isinstance(policy.probability, probability_samplers.SimpleProbability)
