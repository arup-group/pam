from typing import Callable, Dict

import pam.activity
import pam.core


class Filter:
    """Base class for attribute-based filters."""

    def __init__(self):
        pass

    def satisfies_conditions(self, x):
        raise NotImplementedError("{} is a base class".format(type(Filter)))

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
    """Helps filtering Person on specified attributes.

    Parameters
    ----------
    :param conditions
    Dictionary of
    key = person.attribute key
    value = function that returns a boolean given the value at person.attribute[key]

    :param how : {'all', 'any'}, default 'all'
    The level of rigour used to match conditions

    * all: means all conditions for a person need to be met
    * any: means at least one condition needs to be met
    """

    def __init__(self, conditions: Dict[str, Callable[[str], bool]], how="all"):
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
