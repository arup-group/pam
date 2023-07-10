from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY


def test_home_education_home_fill_activity(person_home_education_home):
    person = person_home_education_home
    p_idx, s_idx = person.remove_activity(2)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 1
    assert [p.act for p in person.activities] == ["home"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.has_valid_plan


def test_work_home_work_fill_activity_closed(person_work_home_work_closed):
    person = person_work_home_work_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 1
    assert [p.act for p in person.activities] == ["home"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.has_valid_plan


def test_work_home_shop_work_fill_activity_closed(person_work_home_shop_home_work_closed):
    person = person_work_home_shop_home_work_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 5
    assert [p.act for p in person.activities] == ["home", "shop", "home"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.has_valid_plan


def test_work_home_work_fill_first_activity_not_closed(person_work_home_shop_home_work_not_closed):
    person = person_work_home_shop_home_work_not_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 5
    assert [p.act for p in person.activities] == ["home", "shop", "home"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.has_valid_plan


def test_work_home_work_fill_mid_activity_not_closed(person_work_home_shop_home_work_not_closed):
    person = person_work_home_shop_home_work_not_closed
    duration = person.plan.day[2].duration
    p_idx, s_idx = person.remove_activity(6)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 7
    assert [p.act for p in person.activities] == ["work", "home", "shop", "work"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.plan.day[2].duration > duration  # todo fix bad test
    assert person.has_valid_plan


def test_work_home_work_add_first_activity_not_closed(person_work_home_work_not_closed):
    person = person_work_home_work_not_closed
    p_idx, s_idx = person.remove_activity(0)
    assert person.fill_plan(p_idx, s_idx)
    assert person.length == 3
    assert [p.act for p in person.activities] == ["home", "work"]
    assert person.plan.day[0].start_time == mtdt(0)
    assert person.plan.day[-1].end_time == END_OF_DAY
    assert person.has_valid_plan
