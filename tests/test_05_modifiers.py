from pam.policy.modifiers import RemoveActivity


def test_subclass_name_features_in_repr_string():
    modifier = RemoveActivity([""])
    assert "{}".format(modifier.__class__.__name__) in modifier.__repr__()


def test_subclass_name_features_in_str_string():
    modifier = RemoveActivity([""])
    assert "{}".format(modifier.__class__.__name__) in modifier.__str__()
