"""Location and mode choice models for activity modelling."""

import itertools
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal, NamedTuple, Optional, Union

import numpy as np
import pandas as pd

from pam.activity import Activity, Leg, Plan
from pam.core import Population
from pam.operations.cropping import link_population
from pam.planner.od import OD
from pam.planner.utils_planner import (
    apply_mode_to_home_chain,
    calculate_mnl_probabilities,
    convert_single_anchor_roundtrip,
    get_act_names,
    get_first_leg_time_ratio,
    get_trip_chains_either_anchor,
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

    idxs: list[ChoiceIdx]
    u_choices: np.array
    choice_labels: list[ChoiceLabel]


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

    def sample(self) -> list:
        """Sample from a set of alternative options."""
        sampled = np.apply_along_axis(func1d=self.func_sampling, axis=1, arr=self.probabilities)
        sampled_labels = [self.choice_set.choice_labels[x] for x in sampled]
        self._selections = sampled_labels
        return sampled_labels

    @property
    def selections(self) -> list[ChoiceLabel]:
        if self._selections is None:
            self.sample()
        return self._selections


@dataclass
class ChoiceConfiguration:
    """

    Attributes:
      u (str, optional):
        The utility function specification.
        The string may point to household, person, act, leg, od, or zone data.
        It can also include values and/or mathematical operations.
        Parameters may be passed as single values, or as lists (with each element in the list corresponding to one of the modes in the OD object).
        For example: u='-[0,1] - (2 * od['time']) - (od['time'] * person.attributes['age']>60).
        Defaults to None.
      scope (str, optional): The scope of the function (for example, work activities). Defaults to None.
      func_probabilities (Callable, optional): The function for calculating the probability of each alternative. Defaults to None.
      func_sampling (Callable, optional): The function for sampling across alternatives, ie softmax. Defaults to None.
    """

    u: Optional[str] = None
    scope: Optional[str] = None
    func_probabilities: Optional[Callable] = None
    func_sampling: Optional[Callable] = None

    def validate(self, vars: list[str]) -> None:
        """

        Args:
          vars (list[str]):

        """
        for var in vars:
            if getattr(self, var) is None:
                raise ValueError(f"Setting {var} has not been set yet")


class ChoiceModel:
    def __init__(self, population: Population, od: OD, zones: Union[pd.DataFrame, Zones]) -> None:
        """Choice model interface.

        Args:
            population (Population): A PAM population.
            od (OD): An object holding origin-destination.
            zones (Union[pd.DataFrame, Zones]): Zone-level data.

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

    def configure(self, **kwargs: Optional[Union[str, Callable]]) -> None:
        """Specify the model.

        Args:
          **kwargs (Optional[Union[str, Callable]]): Parameters of the ChoiceConfiguration class.

        """
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = v.replace(" ", "")
            setattr(self.configuration, k, v)
        self.logger.info("Updated model configuration")
        self.logger.info(self.configuration)

    def apply(
        self,
        apply_location: bool = True,
        apply_mode: bool = True,
        once_per_agent: bool = True,
        apply_mode_to: Literal["chain", "previous_leg"] = "chain",
    ) -> None:
        """Apply the choice model to the PAM population,
            updating the activity locations and mode choices in scope.

        Args:
          apply_location (bool, optional): Whether to update activities' location. Defaults to True.
          apply_mode (bool, optional): Whether to update travel modes. Defaults to True.
          once_per_agent (bool, optional): If True, the same selected option is applied to all activities within scope of an agent. Defaults to True.
          apply_mode_to (Literal["chain", "previous_leg"]):
            Whether to apply the mode to the entire trip chain that contains the activity, or the leg preceding the activity.
            Defaults to "chain".

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


class DiscretionaryTrips:
    def __init__(self, plan: Plan, od: OD) -> None:
        """Solve discretionary trip location choice of a PAM plan.

        Args:
            plan (Plan): PAM plan.
            od (OD): An object holding origin-destination matrices.
        """
        self._plan = plan
        self._od = od

    def update_plan(self):
        """Update the locations (in-place) of each non-mandatory activity location in the plan."""
        trip_chains = get_trip_chains_either_anchor(self._plan)
        for trip_chain in trip_chains:
            # if only one achor, convert to round-trip
            convert_single_anchor_roundtrip(trip_chain)
            act_names = get_act_names(trip_chain)
            if len(act_names) > 2:
                if act_names[0] != act_names[-1]:
                    DiscretionaryTripOD(trip_chain=trip_chain, od=self._od).update_plan()
                else:
                    DiscretionaryTripRound(trip_chain=trip_chain, od=self._od).update_plan()


class DiscretionaryTrip(ABC):
    def __init__(self, trip_chain: list[Union[Activity, Leg]], od: OD) -> None:
        """Location choice for discretionary trips in a trip chain.

        Cases:
            1. O->discretionary->O (DiscretionaryTripRound)
            2. O->discretionary->D (DiscretionaryTripOD)
            3. O->discretionary->discretionary->O
            4. O->discretionary->discretionary->D

        Chains with multiple discretionary trips are solved recursively,
            updating the first location each time, and then keeping it fixed as we solve downstream.

        Args:
            trip_chain (list[Union[Activity, Leg]]): A trip chain between two long-term activities.
            od (OD): An object holding origin-destination matrices.
        """
        self._trip_chain = trip_chain
        self._od = od
        self.act_names = get_act_names(trip_chain)

        # anchor points
        self.anchor_zone_start = trip_chain[0].location.area
        self.anchor_zone_end = trip_chain[-1].location.area
        self.trmode = trip_chain[1].mode

        # some checks
        if len(trip_chain) % 2 == 0:
            raise ValueError(
                "Trip chain must have an odd number of elements as it is a sequence of activities joined by trip legs"
            )
        if not all(isinstance(i, Leg) for i in trip_chain[1::2]):
            raise TypeError("Each odd element in the trip chain should be a leg")
        if not all(isinstance(i, Activity) for i in trip_chain[::2]):
            raise TypeError("Each even element in the trip chain should be an activity")

    @abstractmethod
    def choose_destination(self) -> str:
        """Selects a destination for the discretionary activity.

        Returns:
            str: Selected destination zone name.
        """

    def update_plan(self):
        """
        Update the PAM activity locations of the first activity in the trip chain,
        and continue downstream until the entire chain is solved.
        """
        if len(self.act_names) > 2:
            # update locations
            area = self.choose_destination()
            self._trip_chain[2].location.area = area
            self._trip_chain[1].end_location.area = area
            self._trip_chain[3].start_location.area = area

            # if the remaining chain is now a round-trip:
            if self.act_names[0] == self.act_names[-1]:
                # continue downstream recursively
                # with a round-trip selection
                DiscretionaryTripRound(trip_chain=self._trip_chain[2:], od=self._od).update_plan()
            # otherwise, if it is a trip chain with two anchors:
            else:
                # continue downstream recursively
                # the newly-selected location now becomes the first anchor
                DiscretionaryTripOD(trip_chain=self._trip_chain[2:], od=self._od).update_plan()

    @property
    def od(self) -> OD:
        return self._od


class DiscretionaryTripRound(DiscretionaryTrip):
    """
    Location choice for a single discretionary trip, where we have the same anchor at the start and end of the chain.

    The class infers the location of the first discretionary activity in the trip chain.
    """

    def choose_destination(self) -> str:
        """Selects a destination for the discretionary activity.

        Returns:
            str: Selected destination zone name.
        """
        assert isinstance(self._trip_chain[1], Leg)
        destination_p = self._od["od_probs", self.anchor_zone_start, :, self.trmode]
        destination_p = destination_p / destination_p.sum()
        zone = sample_weighted(destination_p)
        area = self._od.labels.destination_zones[zone]

        return area


class DiscretionaryTripOD(DiscretionaryTrip):
    """Location choice for a single discretionary trip, where we have different anchors at the start and end of the chain.

    The class infers the location of the first trip in the trip chain.

    Methodology:
        We combine three conditions:

        1. Distribution of leg compared to total trip
        2. Diversion factor (compared to direct trips)
        3. Zone attraction

        Final probabilities are defined as (1) * (2) * (3) (and then normalised to sum up to 1).

    """

    @staticmethod
    def pdf_leg_ratio(leg_ratios: np.array, observed_ratio: float) -> np.array:
        return np.interp(leg_ratios, [0, observed_ratio, 1], [0, 1, 0])

    @staticmethod
    def pdf_leg_diversion(diversions: np.array, max_diversion_factor: float = 2.1) -> np.array:
        return np.interp(diversions, [1, max_diversion_factor], [1, 0])

    @property
    def observed_leg_ratio(self):
        return get_first_leg_time_ratio(self._trip_chain)

    @property
    def leg_ratios(self) -> np.array:
        """
        Get the impedance ratio between the fist leg candidate locations
            and the corresponding total distance (anchor->discretionary->anchor).

        Returns:
            np.array: An array of the leg time ratios for each candidate intermediate destination.

        """
        imp_first_leg = self._od["time", self.anchor_zone_start, :, self.trmode]
        imp_second_leg = self._od["time", :, self.anchor_zone_end, self.trmode]
        leg_ratio = imp_first_leg / (imp_first_leg + imp_second_leg)

        return leg_ratio

    @property
    def leg_ratio_p(self) -> np.array:
        """
        Get destination probabilities given the leg ratio.

        Returns:
            np.array: An array of the leg time ratio probabilities for each candidate intermediate destination.

        """
        return self.pdf_leg_ratio(
            leg_ratios=self.leg_ratios, observed_ratio=self.observed_leg_ratio
        )

    @property
    def diversion_factors(self) -> np.array:
        """
        Calculate the diversion factor for each potential destination (as compared to a direct trip between anchors).

        Returns:
            np.array: An array of the time diversion factors for each candidate intermediate destination.

        """
        imp_tour = (
            self._od["time", self.anchor_zone_start, :, self.trmode]
            + self._od["time", :, self.anchor_zone_end, self.trmode]
        )
        imp_direct = self._od["time", self.anchor_zone_start, self.anchor_zone_end, self.trmode]
        diversion_factors = imp_tour / imp_direct

        return diversion_factors

    @property
    def diversion_p(self) -> np.array:
        """Diversion factor probabilities

        Returns:
            np.array: An array of the time diversion factor probabilities for each candidate intermediate destination.

        """
        return self.pdf_leg_diversion(self.diversion_factors, max_diversion_factor=2.1)

    @property
    def attraction_p(self):
        """Attraction probabilities."""
        probs = self._od["od_probs", self.anchor_zone_start, :, self.trmode]
        probs = probs / probs.sum()
        return probs

    @property
    def destination_p(self) -> np.array:
        """Get the destination probabilities.

        Combines the leg ratio, diversion, and attraction factors probabilities by calculating their product.

        Returns:
            np.array: Final destination probabilities.
        """
        p = self.leg_ratio_p * self.diversion_p * self.attraction_p
        p /= p.sum()
        return p

    def choose_destination(self) -> str:
        """Selects a destination for the discretionary activity.

        Returns:
            str: Selected destination zone name.
        """
        zone = sample_weighted(self.destination_p)
        area = self._od.labels.destination_zones[zone]

        return area
