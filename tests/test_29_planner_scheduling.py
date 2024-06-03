import numpy as np
import pytest
from pam.planner.choice_scheduling import (
    ActivityDurationMixture,
    ActivityDurationRegression,
    ScheduleModelSimple,
)
from pam.planner.encoder import PlansSequenceEncoder
from tensorflow import keras


@pytest.fixture
def model_simple(population_simple) -> ScheduleModelSimple:
    return ScheduleModelSimple(population_simple)


@pytest.fixture
def plans_encoded(population_simple) -> PlansSequenceEncoder:
    return PlansSequenceEncoder(population_simple)


def test_start_end_tokens(model_simple):
    assert model_simple.encoder.activity_encoder.label_code["SOS"] == 1
    assert model_simple.encoder.activity_encoder.label_code["EOS"] == 2


def test_prediction_shape_matches_input(model_simple, population_simple):
    model_simple.fit(epochs=2)
    y_pred = model_simple.predict(population_simple)
    np.testing.assert_equal(y_pred.shape, model_simple.encoder.durations.shape)


def test_model_built(model_simple):
    assert isinstance(model_simple.model, keras.models.Model)


def test_activity_duration_regression(plans_encoded):
    acts = plans_encoded.acts[:, [0]]
    durations = plans_encoded.durations[:, 0]
    model = ActivityDurationRegression(acts=acts, durations=durations)
    model.fit(epochs=1)
    y_pred = model.predict(acts)
    assert (y_pred < 0).sum() == 0
    assert (y_pred > 1).sum() == 0
    assert y_pred.shape == (len(durations), 1)


def test_activity_duration_mixture(plans_encoded):
    acts = plans_encoded.acts[:, [0]]
    durations = plans_encoded.durations[:, 0]
    model = ActivityDurationMixture(acts=acts, durations=durations)
    model.fit(epochs=1)
    y_pred = model.predict(acts)
    assert (y_pred < 0).sum() == 0
    assert (y_pred > 1).sum() == 0
    assert y_pred.shape == (len(durations), 1)
