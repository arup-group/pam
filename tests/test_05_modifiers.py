import pytest
from pam.policy.modifiers import Modifier, RemoveActivity


def test_Modifier_throws_exception_when_used(Bobby):
    modifier = Modifier()
    with pytest.raises(NotImplementedError) as e:
        modifier.apply_to(Bobby)
    assert '<class \'type\'> is a base class' in str(e.value)


def test_subclass_name_features_in_repr_string():
    modifier = RemoveActivity([''])
    assert '{}'.format(modifier.__class__.__name__) in modifier.__repr__()


def test_subclass_name_features_in_str_string():
    modifier = RemoveActivity([''])
    assert '{}'.format(modifier.__class__.__name__) in modifier.__str__()
