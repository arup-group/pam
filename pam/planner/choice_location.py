"""Location and mode choice models for activity modelling."""
import itertools
import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, List, NamedTuple, Optional, Union

import numpy as np
import pandas as pd

from pam.activity import Activity
from pam.core import Population
from pam.operations.cropping import link_population
from pam.planner.od import OD
from pam.planner.utils_planner import (
    apply_mode_to_home_chain,
    calculate_mnl_probabilities,
    sample_weighted,
)
from pam.planner.zones import Zones


class ChoiceLabel(NamedTuple):
    """Destination and mode choice labels of a selected option."""

    destination: str
    mode: str


class ChoiceIdx(NamedTuple):
    """Choice set index."""

    pid: str
    hid: str
    seq: int
    act: Activity


class ChoiceSet(NamedTuple):
    """MNL Choice set."""

    idxs: List[ChoiceIdx]
    u_choices: np.array
    choice_labels: List[ChoiceLabel]


@dataclass
class SelectionSet:
    """Calculate probabilities and select alternative."""

    choice_set: ChoiceSet
    func_probabilities: Callable
    func_sampling: Optional[Callable] = None
    _selections = None

    @property
    def probabilities(self) -> np.array:
        """Probabilities for each alternative."""
        return np.apply_along_axis(
            func1d=self.func_probabilities, axis=1, arr=self.choice_set.u_choices
        )

    def sample(self) -> List:
        """Sample from a set of alternative options."""
        sampled = np.apply_along_axis(func1d=self.func_sampling, axis=1, arr=self.probabilities)
        sampled_labels = [self.choice_set.choice_labels[x] for x in sampled]
        self._selections = sampled_labels
        return sampled_labels

    @property
    def selections(self) -> List[ChoiceLabel]:
        if self._selections is None:
            self.sample()
        return self._selections


@dataclass
class ChoiceConfiguration:
    """:param u: The utility function specification, defined as a string.
        The string may point to household, person, act, leg,
            od, or zone data.
        It can also include values and/or mathematical operations.
        Parameters may be passed as single values, or as lists
            (with each element in the list corresponding to one of the modes in the OD object)
        For example: u='-[0,1] - (2 * od['time']) - (od['time'] * person.attributes['age']>60)
    :param scope: The scope of the function (for example, work activities).
    :param func_probabilities: The function for calculating the probability of each alternative
    :param func_sampling: The function for sampling across alternatives, ie softmax
    """

    u: Optional[str] = None
    scope: Optional[str] = None
    func_probabilities: Optional[Callable] = None
    func_sampling: Optional[Callable] = None

    def validate(self, vars: List[str]) -> None:
        """Return an error if a value has not been set."""
        for var in vars:
            if getattr(self, var) is None:
                raise ValueError(f"Setting {var} has not been set yet")


class ChoiceModel:
    def __init__(self, population: Population, od: OD, zones: Union[pd.DataFrame, Zones]) -> None:
        """Choice model interface.

        :param population: A PAM population.
        :param od: An object holding origin-destination.
        :param zones: Zone-level data.
        """
        self.logger = logging.getLogger(__name__)
        self.population = population
        link_population(self.population)
        self.od = od
        self.zones = self.parse_zone_data(zones)
        self.zones.data = self.zones.data.loc[list(od.labels.destination_zones)]
        self.configuration = ChoiceConfiguration()
        self._selections = None

    @staticmethod
    def parse_zone_data(zones: Union[pd.DataFrame, Zones]) -> Zones:
        if isinstance(zones, Zones):
            return deepcopy(zones)
        elif isinstance(zones, pd.DataFrame):
            return Zones(data=zones.copy())

    def configure(self, **kwargs) -> None:
        """Specify the model.

        :Keyword Arguments: Parameters of the ChoiceConfiguration class.
        """
        for k, v in kwargs.items():
            if type(v) == str:
                v = v.replace(" ", "")
            setattr(self.configuration, k, v)
        self.logger.info("Updated model configuration")
        self.logger.info(self.configuration)

    def apply(
        self, apply_location=True, apply_mode=True, once_per_agent=True, apply_mode_to="chain"
    ):
        """Apply the choice model to the PAM population,
            updating the activity locations and mode choices in scope.

        :param apply_location: Whether to update activities' location
        :param apply_mode: Whether to update travel modes
        :param once_per_agent: If True, the same selected option
            is applied to all activities within scope of an agent.
        :param apply_mode_to: `chain` or `previous_leg`:
            Whether to apply the mode to the entire trip chain
            that contains the activity,
            or the leg preceding the activity.
        """
        self.logger.info("Applying choice model...")
        self.logger.info(f"Configuration: \n{self.configuration}")

        pid = None
        destination = None
        trmode = None

        # update location and mode
        for idx, selection in zip(self.selections.choice_set.idxs, self.selections.selections):
            if not (once_per_agent and (pid == idx.pid)):
                destination = selection.destination
                trmode = selection.mode

            pid = idx.pid
            act = idx.act

            if apply_location:
                act.location.area = destination

            if apply_mode and (act.previous is not None):
                if apply_mode_to == "chain":
                    apply_mode_to_home_chain(act, trmode)
                elif apply_mode_to == "previous_leg":
                    act.previous.mode = trmode
                else:
                    raise ValueError(f"Invalid option {apply_mode_to}")

        self.logger.info("Choice model application complete.")

    def get_choice_set(self) -> ChoiceSet:
        """Construct an agent's choice set for each activity/leg within scope."""
        self.configuration.validate(["u", "scope"])
        od = self.od
        u = self.configuration.u
        scope = self.configuration.scope
        # zones might be defined in `u` and so be required on calling `eval(u)`
        zones = self.zones  # noqa: F841

        idxs = []
        u_choices = []
        choice_labels = list(itertools.product(od.labels.destination_zones, od.labels.mode))
        choice_labels = [ChoiceLabel(*x) for x in choice_labels]

        # iterate across activities
        for hid, hh in self.population:
            for pid, person in hh:
                for i, act in enumerate(person.activities):
                    if eval(scope):
                        idx_act = ChoiceIdx(pid=pid, hid=hid, seq=i, act=act)
                        # calculate utilities for each alternative
                        u_act = eval(u)
                        # flatten location-mode combinations
                        u_act = u_act.flatten()

                        u_choices.append(u_act)
                        idxs.append(idx_act)

        u_choices = np.array(u_choices)

        # check dimensions
        assert u_choices.shape[1] == len(choice_labels)
        assert u_choices.shape[0] == len(idxs)

        return ChoiceSet(idxs=idxs, u_choices=u_choices, choice_labels=choice_labels)

    @property
    def selections(self) -> SelectionSet:
        self.configuration.validate(["func_probabilities", "func_sampling"])
        if self._selections is None:
            self._selections = SelectionSet(
                choice_set=self.get_choice_set(),
                func_probabilities=self.configuration.func_probabilities,
                func_sampling=self.configuration.func_sampling,
            )
        return self._selections


class ChoiceMNL(ChoiceModel):
    """Applies a Multinomial Logit Choice model."""

    def __init__(self, population: Population, od: OD, zones: pd.DataFrame) -> None:
        super().__init__(population, od, zones)
        self.configure(
            func_probabilities=calculate_mnl_probabilities, func_sampling=sample_weighted
        )
