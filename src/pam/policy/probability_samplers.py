import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Optional, Union

import pam.activity
import pam.core


class SamplingProbability(ABC):
    """Base class for probabilistic samplers."""

    def __init__(self, probability: Union[float, int]):
        if isinstance(probability, int):
            probability = float(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability

    def __repr__(self):
        attribs = vars(self)
        return "<{} instance at {}: {}>".format(
            self.__class__.__name__,
            id(self),
            ", ".join("%r: %r" % item for item in attribs.items()),
        )

    def __str__(self):
        attribs = vars(self)
        return "{} with attributes: {}".format(
            self.__class__.__name__, ", ".join("%s: %s" % item for item in attribs.items())
        )

    def print(self):
        print(self.__str__())

    def sample(self, x):
        return random.random() < self.p(x)

    @abstractmethod
    def p(self, x):
        "Compute probability"


class SimpleProbability(SamplingProbability):
    def __init__(self, probability: Union[float, int]) -> None:
        """A probabilistic sampler which returns value of probability at the same level as the input (household/person/activity).

        Args:
            probability (Union[float, int]): 0<probability<=1.
        """
        super().__init__(probability)

    def p(self, x):
        return self.probability


class HouseholdProbability(SamplingProbability):
    def __init__(
        self,
        probability: Union[float, int, Callable[[pam.core.Household], float]],
        kwargs: Optional[dict] = None,
    ) -> None:
        """A probabilistic sampler which evaluates value of probability at household level based on probability for a household.

        Args:
            probability (Union[float, int, Callable[[pam.core.Household], float]]):
                0<probability<=1, or a function which given input of pam.core.Household returns a float/int: 0<probability<=1 corresponding to the likelihood of the household being sampled.
            kwargs (Optional[dict], optional): Keyword arguments to add when calling `probability`, if it is a Callable. Defaults to None.
        """
        super().__init__(probability)
        assert isinstance(self.probability, float) or callable(self.probability)
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, pam.core.Household):
            return self.compute_probability_for_household(x)
        elif isinstance(x, pam.core.Person):
            raise NotImplementedError
        elif isinstance(x, pam.activity.Activity):
            raise NotImplementedError
        else:
            raise TypeError

    def compute_probability_for_household(self, household):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(household, **self.kwargs)


class PersonProbability(SamplingProbability):
    def __init__(
        self,
        probability: Union[float, int, Callable[[pam.core.Person], float]],
        kwargs: Optional[dict] = None,
    ) -> None:
        """A probabilistic sampler which evaluates value of probability at household and person level based on probability for a person.

        Args:
            probability (Union[float, int, Callable[[pam.core.Person], float]]):
                0<probability<=1 or a function which given input of pam.core.Person returns a float/int: 0<probability<=1 corresponding to the likelihood of the person being sampled.
            kwargs (Optional[dict], optional): Keyword arguments to add when calling `probability`, if it is a Callable. Defaults to None.
        """
        super().__init__(probability)
        assert isinstance(self.probability, float) or callable(self.probability)
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, pam.core.Household):
            p = 1
            for pid, person in x.people.items():
                p *= 1 - self.compute_probability_for_person(person)
            return 1 - p
        elif isinstance(x, pam.core.Person):
            return self.compute_probability_for_person(x)
        elif isinstance(x, pam.activity.Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def compute_probability_for_person(self, person):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(person, **self.kwargs)


class ActivityProbability(SamplingProbability):
    def __init__(
        self,
        activities: list,
        probability: Union[float, int, Callable[[pam.activity.Activity], float]],
        kwargs: Optional[dict] = None,
    ) -> None:
        """A probabilistic sampler which evaluates value of probability at household, person and activity level based on probability for an activity.

        Args:
            activities (list): List of activities.
            probability (Union[float, int, Callable[[pam.activity.Activity]]]):
                A float/int: 0<probability<=1 or a function which given input of pam.core.Activity returns a float/int: 0<probability<=1 corresponding to the likelihood of the activity being sampled.
            kwargs (Optional[dict], optional): Keyword arguments to add when calling `probability`, if it is a Callable. Defaults to None.
        """
        super().__init__(probability)
        self.activities = activities
        assert isinstance(self.probability, float) or callable(self.probability)
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, pam.core.Household):
            p = 1
            for pid, person in x.people.items():
                for act in person.activities:
                    if self.is_relevant_activity(act):
                        p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, pam.core.Person):
            p = 1
            for act in x.activities:
                if self.is_relevant_activity(act):
                    p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, pam.activity.Activity):
            if self.is_relevant_activity(x):
                return self.compute_probability_for_activity(x)
            return 0
        else:
            raise NotImplementedError

    def compute_probability_for_activity(self, activity):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(activity, **self.kwargs)

    def is_relevant_activity(self, act):
        return act.act.lower() in self.activities


def verify_probability(probability, unacceptable_types=None):
    if unacceptable_types is None:
        unacceptable_types = ()
    if isinstance(probability, int):
        probability = float(probability)
    assert not isinstance(
        probability, unacceptable_types
    ), "{} is of type {} which is not accepted. Check your policy's application level.".format(
        probability, type(probability)
    )
    if isinstance(probability, float):
        assert 0 < probability <= 1
        probability = SimpleProbability(probability)
    elif isinstance(probability, list):
        for i in range(len(probability)):
            assert not isinstance(
                probability[i], unacceptable_types
            ), "{} is of type {} which is not accepted. Check your policy's application level".format(
                probability[i], type(probability[i])
            )
            if isinstance(probability[i], float):
                probability[i] = SimpleProbability(probability[i])
    else:
        assert isinstance(
            probability, SamplingProbability
        ), "Probability passed to a policy needs to be float, integer or {}, not {}".format(
            type(SamplingProbability), type(probability)
        )
    return probability
