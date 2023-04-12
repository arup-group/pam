import pytest
import os
from tests.fixtures import Steve
from pam.read import read_matsim
from pam.planner.encoder import StringCharacterEncoder, \
    StringIntEncoder, PlanCharacterEncoder, PlanOneHotEncoder, \
    PlansCharacterEncoder, PlansOneHotEncoder


@pytest.fixture
def acts():
    return ['work', 'home', 'shop']


test_plans = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 "test_data/test_matsim_plansv12.xml")
)


@pytest.fixture
def population():
    population = read_matsim(test_plans, version=12)
    return population


def test_strings_encoded_to_single_characters(acts):
    encoder = StringCharacterEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        assert type(encoded) == str
        assert len(encoded) == 1


def test_strings_encoded_to_integers(acts):
    encoder = StringIntEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        assert type(encoded) == int


@pytest.mark.parametrize('encoder_class', [StringCharacterEncoder, StringIntEncoder])
def test_activity_encoding_works_two_way(acts, encoder_class):
    """ Encoded labels can be converted back to the same value  """
    encoder = encoder_class(acts)
    for act in acts:
        encoded = encoder.encode(act)
        decoded = encoder.decode(encoded)
        assert decoded == act


@pytest.mark.parametrize('encoder_class', [PlanCharacterEncoder, PlanOneHotEncoder])
def test_plan_encoding_works_two_way(Steve, encoder_class):
    """ Encoded plans can be converted back to the original  """
    plan = Steve.plan
    labels = plan.activity_classes
    encoder = encoder_class(labels=labels)
    plan_encoded_decoded = encoder.decode(
        encoder.encode(plan)
    )

    acts = [x.act for x in plan.day]
    acts_ed = [x.act for x in plan_encoded_decoded.day]
    assert acts == acts_ed

    start_times = [x.start_time for x in plan.day]
    start_times_ed = [x.start_time for x in plan_encoded_decoded.day]
    assert start_times == start_times_ed

    end_times = [x.end_time for x in plan.day]
    end_times_ed = [x.end_time for x in plan_encoded_decoded.day]
    assert end_times == end_times_ed


@pytest.mark.parametrize('encoder_class', [PlansCharacterEncoder, PlansOneHotEncoder])
def test_all_plans_are_encoded(population, encoder_class):
    encoder = encoder_class(population.activity_classes)
    plans_encoded = encoder.encode(population.plans())
    assert plans_encoded.shape[0] == len(population)

