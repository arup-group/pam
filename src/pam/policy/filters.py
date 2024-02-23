from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Literal

import pam.activity
import pam.core


class Filter(ABC):
    """Base class for attribute-based filters."""

    def __init__(self):
        pass

    @abstractmethod
    def satisfies_conditions(self, x):
        "Check if object satisfies conditions to be filtered"

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


class PersonAttributeFilter(Filter):
    def __init__(
        self, conditions: dict[str, Callable[[str], bool]], how: Literal["all", "any"] = "all"
    ) -> None:
        """Helps filtering Person on specified attributes.

        Args:
            conditions (dict[str, Callable[[str], bool]]):
                Dictionary of key = person.attribute, value = function that returns a boolean given the value at person.attribute[key]
            how (Literal["all", "any"]):
                The level of rigour used to match conditions.
                `all` means all conditions for a person need to be met. `any` means at least one condition needs to be met

        """
        super().__init__()
        self.conditions = conditions
        self.how = how

    def satisfies_conditions(self, x):
        if isinstance(x, pam.core.Household):
            # household satisfies conditions if one person satisfies conditions according to self.how
            return self.household_satisfies_conditions(x)
        elif isinstance(x, pam.core.Person):
            return self.person_satisfies_conditions(x)
        elif isinstance(x, pam.activity.Activity):
            raise NotImplementedError
        else:
            raise NotImplementedError

    def household_satisfies_conditions(self, household):
        if not self.conditions:
            return True
        for pid, person in household.people.items():
            if self.person_satisfies_conditions(person):
                return True
        return False

    def person_satisfies_conditions(self, person):
        if not self.conditions:
            return True
        elif self.how == "all":
            satisfies_attribute_conditions = True
            for attribute_key, attribute_condition in self.conditions.items():
                satisfies_attribute_conditions &= attribute_condition(
                    person.attributes[attribute_key]
                )
            return satisfies_attribute_conditions
        elif self.how == "any":
            satisfies_attribute_conditions = False
            for attribute_key, attribute_condition in self.conditions.items():
                satisfies_attribute_conditions |= attribute_condition(
                    person.attributes[attribute_key]
                )
            return satisfies_attribute_conditions
        else:
            raise NotImplementedError(
                "{} not implemented, use only `all` or `any`".format(self.how)
            )
