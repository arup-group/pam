import pam.core as core
import pam.activity as activity
from pam.policies import Policy
import random


class SamplingProbability:
    def __init__(self):
        pass

    def sample(self, x):
        return random.random() < self.p(x)

    def p(self, x):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))


class SimpleProbability(SamplingProbability):
    def __init__(self, probability):
        super().__init__()
        assert 0 < probability <= 1
        self.probability = probability

    def p(self, x):
        return self.probability


class HouseholdProbability(SamplingProbability):
    def __init__(self, probability, kwargs=None):
        super().__init__()
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, core.Household):
            return self.compute_probability_for_household(x)
        elif isinstance(x, core.Person):
            raise NotImplementedError
        elif isinstance(x, activity.Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def compute_probability_for_household(self, household):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(household, **self.kwargs)


class PersonProbability(SamplingProbability):
    def __init__(self, probability, kwargs=None):
        super().__init__()
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, core.Household):
            p = 1
            for pid, person in x.people.items():
                p *= 1 - self.compute_probability_for_person(person)
            return 1 - p
        elif isinstance(x, core.Person):
            return self.compute_probability_for_person(x)
        elif isinstance(x, activity.Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def compute_probability_for_person(self, person):
        if isinstance(self.probability, float):
            return self.probability
        elif callable(self.probability):
            return self.probability(person, **self.kwargs)


class ActivityProbability(SamplingProbability):
    def __init__(self, activities : list, probability, kwargs=None):
        super().__init__()
        self.activities = activities
        if isinstance(probability, int):
            probability = float(probability)
        assert isinstance(probability, float) or callable(probability)
        if isinstance(probability, float):
            assert 0 < probability <= 1
        self.probability = probability
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def p(self, x):
        if isinstance(x, core.Household):
            p = 1
            for pid, person in x.people.items():
                for act in person.activities:
                    if self.is_relevant_activity(act):
                        p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, core.Person):
            p = 1
            for act in x.activities:
                if self.is_relevant_activity(act):
                    p *= 1 - self.compute_probability_for_activity(act)
            return 1 - p
        elif isinstance(x, activity.Activity):
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


def verify_probability(probability, acceptable_types):
    if isinstance(probability, int):
        probability = float(probability)
    assert isinstance(probability, acceptable_types)
    if isinstance(probability, float):
        assert 0 < probability <= 1
        probability = SimpleProbability(probability)
    elif isinstance(probability, list):
        for i in range(len(probability)):
            assert isinstance(
                probability[i], acceptable_types)
            if isinstance(probability[i], float):
                probability[i] = SimpleProbability(probability[i])
    return probability
