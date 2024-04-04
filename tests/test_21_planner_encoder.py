import pytest
from pam.planner.encoder import (
    PlanCharacterEncoder,
    PlanOneHotEncoder,
    PlansCharacterEncoder,
    PlansOneHotEncoder,
    StringCharacterEncoder,
    StringIntEncoder,
)


@pytest.fixture
def acts():
    return ["work", "home", "shop"]


def test_strings_encoded_to_single_characters(acts):
    encoder = StringCharacterEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        assert isinstance(encoded, str)
        assert len(encoded) == 1


def test_strings_encoded_to_integers(acts):
    encoder = StringIntEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        assert isinstance(encoded, int)


@pytest.mark.parametrize("encoder_class", [StringCharacterEncoder, StringIntEncoder])
def test_activity_encoding_works_two_way(acts, encoder_class):
    """Encoded labels can be converted back to the same value."""
    encoder = encoder_class(acts)
    for act in acts:
        encoded = encoder.encode(act)
        decoded = encoder.decode(encoded)
        assert decoded == act


@pytest.mark.parametrize("encoder_class", [PlanCharacterEncoder, PlanOneHotEncoder])
def test_plan_encoding_works_two_way(Steve, encoder_class):
    """Encoded plans can be converted back to the original."""
    plan = Steve.plan
    labels = plan.activity_classes
    encoder = encoder_class(labels=labels)
    plan_encoded_decoded = encoder.decode(encoder.encode(plan))

    acts = [x.act for x in plan.day]
    acts_ed = [x.act for x in plan_encoded_decoded.day]
    assert acts == acts_ed

    start_times = [x.start_time for x in plan.day]
    start_times_ed = [x.start_time for x in plan_encoded_decoded.day]
    assert start_times == start_times_ed

    end_times = [x.end_time for x in plan.day]
    end_times_ed = [x.end_time for x in plan_encoded_decoded.day]
    assert end_times == end_times_ed


@pytest.mark.parametrize("encoder_class", [PlansCharacterEncoder, PlansOneHotEncoder])
def test_all_plans_are_encoded(population_no_args, encoder_class):
    encoder = encoder_class(population_no_args.activity_classes)
    plans_encoded = encoder.encode(population_no_args.plans())
    assert plans_encoded.shape[0] == len(population_no_args)


def test_one_hot_encoder_shape(Steve):
    plan = Steve.plan
    labels = plan.activity_classes
    encoder = PlanOneHotEncoder(labels=labels)
    plan_encoded = encoder.encode(plan)

    assert plan_encoded.shape == (len(labels) + 1, 24 * 60)
    assert plan_encoded.dtype == bool
    assert (plan_encoded.sum(axis=0) == 1).all()


def test_character_encoder_shape(Steve):
    plan = Steve.plan
    labels = plan.activity_classes
    encoder = PlanCharacterEncoder(labels=labels)
    plan_encoded = encoder.encode(plan)

    assert len(plan_encoded) == 24 * 60
    assert isinstance(plan_encoded, str)
