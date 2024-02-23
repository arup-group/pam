from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pam.activity import Plan

from datetime import timedelta as td
from itertools import groupby
from typing import List, Optional, Union

import numpy as np

from pam import activity
from pam.variables import START_OF_DAY


class Encoder:
    def __init__(self, labels: List[str], travel_act="travel") -> None:
        self.labels = set(labels)
        if travel_act not in self.labels:
            self.labels.add(travel_act)
        self.label_code = self.get_mapping(self.labels)
        self.code_label = {v: k for k, v in self.label_code.items()}

    def encode(self, label: str) -> Union[int, str]:
        return self.label_code[label]

    def decode(self, code: Union[int, str]) -> str:
        return self.code_label[code]

    @staticmethod
    def get_mapping(labels: List[str]):
        raise NotImplementedError


class StringCharacterEncoder(Encoder):
    """Encodes strings as single characters."""

    @staticmethod
    def get_mapping(labels: List[str]) -> dict:
        encoded = {}
        for i, act in enumerate(labels):
            encoded[act] = chr(i + 65)
        return encoded


class StringIntEncoder(Encoder):
    """Encodes strings as integers."""

    @staticmethod
    def get_mapping(labels: List[str]) -> dict:
        encoded = {label: i for i, label in enumerate(labels)}
        return encoded


class PlanEncoder:
    activity_encoder_class = None

    def __init__(
        self,
        activity_encoder: Optional[StringCharacterEncoder] = None,
        labels: Optional[List[str]] = None,
    ) -> None:
        if activity_encoder is not None:
            self.activity_encoder = activity_encoder
        elif labels is not None:
            self.activity_encoder = self.activity_encoder_class(labels)
        else:
            raise ValueError("Please provide appropriate activity labels or encodings")

    @staticmethod
    def add_plan_component(plan: Plan, seq, act, start_time, duration) -> None:
        if act == "travel":
            plan.add(activity.Leg(seq=seq, start_time=start_time, end_time=start_time + duration))
        else:
            plan.add(
                activity.Activity(
                    seq=seq, act=act, start_time=start_time, end_time=start_time + duration
                )
            )

    def encode(self):
        raise NotImplementedError

    def decode(self, encoded_plan: np.array) -> Plan:
        """Decode a sequence to a new PAM plan."""
        start_time = START_OF_DAY
        plan = activity.Plan()
        # for every activity/leg:
        for seq, (k, g) in enumerate(groupby(self.get_seq(encoded_plan))):
            duration = td(minutes=len(list(g)))
            act = self.activity_encoder.decode(k)
            # add to the plan and advance start time
            self.add_plan_component(
                plan=plan, seq=seq, act=act, start_time=start_time, duration=duration
            )
            start_time += duration

        return plan

    @staticmethod
    def get_seq(x):
        raise NotImplementedError


class PlanCharacterEncoder(PlanEncoder):
    activity_encoder_class = StringCharacterEncoder

    def encode(self, plan: Plan) -> np.array:
        """Convert a pam plan to a character sequence."""
        encoded = ""
        for act in plan.day:
            duration = int(act.duration / td(minutes=1))
            encoded = encoded + (self.activity_encoder.encode(act.act) * duration)

        return encoded

    @staticmethod
    def get_seq(x):
        return x


class PlanOneHotEncoder(PlanEncoder):
    activity_encoder_class = StringIntEncoder

    def encode(self, plan: Plan) -> np.array:
        """Encode a PAM plan into a 2D numpy boolean array,
        where the row indicates the activity
        and the column indicates the minute of the day.
        """
        duration = int((plan.day[-1].end_time - START_OF_DAY) / td(minutes=1))
        encoded = np.zeros(shape=(len(self.activity_encoder.labels), duration), dtype=bool)
        for act in plan.day:
            start_minute = int((act.start_time - START_OF_DAY) / td(minutes=1))
            end_minute = int((act.end_time - START_OF_DAY) / td(minutes=1))
            idx = self.activity_encoder.encode(act.act)
            encoded[idx, start_minute:end_minute] = True

        return encoded

    @staticmethod
    def get_seq(x):
        return x.argmax(axis=0)


class PlansEncoder:
    plans_encoder_class = None
    dtype = None

    def __init__(self, activity_classes: set) -> None:
        self.plan_encoder = self.plans_encoder_class(labels=activity_classes)

    def encode(self, plans: List[Plan]) -> np.ndarray:
        """Encode all plans to a stacked numpy array."""
        plans_encoded = np.stack([self.plan_encoder.encode(x) for x in plans])
        return plans_encoded


class PlansCharacterEncoder(PlansEncoder):
    plans_encoder_class = PlanCharacterEncoder


class PlansOneHotEncoder(PlansEncoder):
    """Encode plans to a 3D numpy array,
    where the first axis indicates the person,
    the second indicates the activity,
    and the third indicates the minute of the day.
    """

    plans_encoder_class = PlanOneHotEncoder
