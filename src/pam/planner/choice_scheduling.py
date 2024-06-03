from typing import Optional

import numpy as np
from tensorflow import keras

from pam.core import Population
from pam.planner.encoder import PlansSequenceEncoder


class ScheduleModelSimple:
    def __init__(
        self, population: Population, n_units: Optional[int] = 50, dropout: Optional[float] = 0.1
    ) -> None:
        self.encoder = PlansSequenceEncoder(population=population)

        # build model
        input_acts = keras.layers.Input(shape=[self.encoder.acts.shape[1]])
        emb_acts = keras.layers.Embedding(
            len(self.encoder.activity_encoder.labels), 1, mask_zero=True, name="emb"
        )(input_acts)
        encoder_h1, encoder_h, encoder_c = keras.layers.LSTM(
            n_units, return_state=True, name="encoder_h1"
        )(emb_acts)
        encoder_state = [encoder_h, encoder_c]

        decoder_input = keras.layers.Input(shape=[self.encoder.durations.shape[1] - 1, 1])
        decoder_h1 = keras.layers.LSTM(
            n_units, name="decoder_h1", dropout=dropout, return_sequences=True
        )(decoder_input, initial_state=encoder_state)
        decoder_h2 = keras.layers.LSTM(
            n_units, name="decoder_h2", dropout=dropout, return_sequences=True
        )(decoder_h1)
        decoder_output = keras.layers.Dense(1, activation="relu", name="decoder_output")(decoder_h2)
        model = keras.models.Model(inputs=[input_acts, decoder_input], outputs=[decoder_output])

        model.compile(loss="mean_squared_error", optimizer="adam", metrics=["accuracy"])
        model.summary()

        self.model = model

    def fit(self, epochs: int = 500) -> None:
        """Fit the sceduling model.

        Args:
            epochs (int, optional): Number of epochs to run. Defaults to 500.
        """
        X = self.encoder.acts[:, ::-1]
        durations = self.encoder.durations
        self.history = self.model.fit([X, durations[:, :-1]], durations[:, 1:], epochs=epochs)

    def predict(self, population: Population) -> np.array:
        """Predict the activity durations of a population.

        Args:
            population (Population): A PAM population.

        Returns:
            np.array: Durations array. Each row represents a plan.
        """
        encoder = PlansSequenceEncoder(
            population=population, activity_encoder=self.encoder.activity_encoder
        )
        X = encoder.acts[:, ::-1]
        y_pred = np.zeros(shape=encoder.durations.shape)
        for i in range(1, y_pred.shape[1]):
            y_pred[:, i] = self.model.predict([X, y_pred[:, :i]])[:, -1, 0]

        return y_pred
