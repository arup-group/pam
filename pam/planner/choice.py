"""
Choice models for activity synthesis
"""
from typing import Optional
import pandas as pd
from pam.planner.od import OD
from pam.core import Population
from pam.operations.cropping import link_population
from copy import deepcopy

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
        self.population = population
        link_population(self.population)
        self.od = od
        self.zones = zones.loc[od.labels.destination_zones].copy()

    def configure():
        raise NotImplementedError

    def apply():
        raise NotImplementedError


class ChoiceMNL(ChoiceModel):
    """
    Implements a Multinomial Logit Choice model
    """
    def configure():
        pass

    def apply():
        pass
