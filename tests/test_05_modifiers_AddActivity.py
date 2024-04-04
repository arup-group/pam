import pytest
from pam.activity import Activity
from pam.policy import modifiers
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def assert_correct_activities(person, ordered_activities_list):
    assert len(person.plan) % 2 == 1
    for i in range(0, len(person.plan), 2):
        assert isinstance(person.plan.day[i], Activity)
    assert [a.act for a in person.plan.activities] == ordered_activities_list
    assert person.plan[0].start_time == mtdt(0)
    assert person.plan[len(person.plan) - 1].end_time == END_OF_DAY


def test_AddActivity_throws_exception_if_apply_to_given_wrong_input(Bobby):
    policy = modifiers.AddActivity([""])
    with pytest.raises(NotImplementedError) as e:
        policy.apply_to(Bobby)
    assert "Watch this space" in str(e.value)
