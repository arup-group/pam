def test_home_education_home_remove_activity_education(person_home_education_home):
    person = person_home_education_home
    p_idx, s_idx = person.remove_activity(2)
    assert p_idx == 0
    assert s_idx == 3
    assert [p.act for p in person.activities] == ["home", "home"]


def test_work_home_work_remove_first_activity_closed(person_work_home_work_closed):
    person = person_work_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx == 1
    assert s_idx == 1
    assert [p.act for p in person.activities] == ["home"]


def test_work_home_work_remove_last_activity_closed(person_work_home_work_closed):
    person = person_work_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(4)
    assert p_idx == 1
    assert s_idx == 1
    assert [p.act for p in person.activities] == ["home"]


def test_work_home_work_shop_remove_first_activity_closed(person_work_home_shop_home_work_closed):
    person = person_work_home_shop_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx == 5
    assert s_idx == 1
    assert [p.act for p in person.activities] == ["home", "shop", "home"]


def test_work_home_work_shop_remove_last_activity_closed(person_work_home_shop_home_work_closed):
    person = person_work_home_shop_home_work_closed
    assert person.closed_plan
    p_idx, s_idx = person.remove_activity(8)
    assert p_idx == 5
    assert s_idx == 1
    assert [p.act for p in person.activities] == ["home", "shop", "home"]


def test_work_home_work_remove_first_activity_not_closed(person_work_home_work_not_closed):
    person = person_work_home_work_not_closed
    assert not person.closed_plan
    p_idx, s_idx = person.remove_activity(0)
    assert p_idx is None
    assert s_idx == 1
    assert [p.act for p in person.activities] == ["home", "work"]


def test_work_home_work_remove_last_activity_not_closed(person_work_home_work_not_closed):
    person = person_work_home_work_not_closed
    assert not person.closed_plan
    p_idx, s_idx = person.remove_activity(4)
    assert p_idx == 2
    assert s_idx is None
    assert [p.act for p in person.activities] == ["work", "home"]
