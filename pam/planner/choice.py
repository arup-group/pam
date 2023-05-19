"""
Choice models for activity synthesis
"""
from dataclasses import dataclass
from functools import lru_cache, cached_property
import itertools
import logging
from typing import Optional, List, NamedTuple, Callable
import pandas as pd
import numpy as np
from pam.planner.od import OD
from pam.planner.utils_planner import calculate_mnl_probabilities, sample_weighted
from pam.core import Population
from pam.operations.cropping import link_population
from copy import deepcopy


class ChoiceSet(NamedTuple):
    """ MNL Choice set  """
    idxs: List
    u_choices: np.array
    choice_labels: List[tuple]


@dataclass
class SelectionSet:
    """ Calculate probabilities and select alternative """
    choice_set: ChoiceSet
    func_probabilities: Callable
    func_selection: Callable
    _selections = None

    @cached_property
    def probabilities(self) -> np.array:
        """
        Probabilities for each alternative.
        """
        return np.apply_along_axis(
            func1d=self.func_probabilities,
            axis=1,
            arr=self.choice_set.u_choices
        )

    def sample(self):
        sampled = np.apply_along_axis(
            func1d=self.func_selection,
            axis=1,
            arr=self.probabilities
        )
        sampled_labels = [self.choice_set.choice_labels[x] for x in sampled]
        self._selections = sampled_labels
        return sampled_labels

    @property
    def selections(self):
        if self._selections is None:
            self.sample()
        return self._selections


class ChoiceModel:

    def __init__(
            self,
            population: Population,
            od: OD,
            zones: pd.DataFrame
    ) -> None:
        """
        Choice model interface.

        :param population: A PAM population.
        :param od: An object holding origin-destination.
        :param zones: Zone-level data.
        """
        self.logger = logging.getLogger(__name__)
        self.population = population
        link_population(self.population)
        self.od = od
        self.zones = zones.loc[od.labels.destination_zones].copy()

        self.u = None
        self.scope = None
        self.func_probabilities = None
        self.func_selection = None

    def configure(
            self,
            u: str,
            scope: str,
            func_probabilities: Optional[Callable] = None,
            func_selection: Optional[Callable] = None
    ):
        """
        Specify the model. 

        :param u: The utility function specification, defined as a string. 
            The string may point to household, person, act, leg, 
                od, or zone data. 
            It can also include values and/or mathematical operations.
            Parameters may be passed as single values, or as lists 
                (with each element in the list corresponding to one of the modes in the OD object)
            For example: u='-[0,1] - (2 * od['time']) - (od['time'] * person.attributes['age']>60)
        :param scope: The scope of the function (for example, work activities).
        """
        self.u = u
        self.scope = scope
        if func_probabilities is not None:
            self.func_probabilities = func_probabilities
        if func_selection is not None:
            self.func_selection = func_selection

    def apply(self, apply_location=True, apply_mode=True):
        """
        Apply the choice model to the PAM population, 
            updating the activity locations and mode choices in scope.
        """
        self.logger.info('Applying choice model...')
        
        selections = self.get_selections()
        for idx, s in zip(selections.choice_set.idxs, selections.selections):
            act = idx['act']
            if apply_location:
                act.location.area = s[0]
            if apply_mode and (act.previous is not None):
                act.previous.mode = s[1]

    def get_choice_set(self) -> ChoiceSet:
        """
        Construct an agent's choice set for each activity/leg within scope.
        """
        od = self.od
        zones = self.zones
        u = self.u
        scope = self.scope

        idxs = []
        u_choices = []
        choice_labels = list(itertools.product(
            od.labels.destination_zones,
            od.labels.mode
        ))

        # iterate across activities
        for hid, hh in self.population:
            for pid, person in hh:
                for i, act in enumerate(person.activities):
                    if eval(scope):
                        idx_act = {
                            'pid': pid,
                            'hid': hid,
                            'seq': i,
                            'act': act
                        }
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

    def get_selections(self) -> SelectionSet:
        selections = SelectionSet(
            choice_set=self.get_choice_set(),
            func_probabilities=self.func_probabilities,
            func_selection=self.func_selection
        )
        return selections


class ChoiceMNL(ChoiceModel):
    """
    Implements a Multinomial Logit Choice model
    """

    def __init__(self, population: Population, od: OD, zones: pd.DataFrame) -> None:
        super().__init__(population, od, zones)
        self.func_probabilities = calculate_mnl_probabilities
        self.func_selection = sample_weighted
