import pytest
from pam.planner.encoder import StringCharacterEncoder

@pytest.fixture
def acts():
    return ['work', 'home', 'shop']

def test_strings_encoded_to_single_characters(acts):
    encoder = StringCharacterEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        assert type(encoded) == str
        assert len(encoded)==1

def test_encoding_works_two_way(acts):
    """ Encoded labels can be converted back to the same value  """
    encoder = StringCharacterEncoder(acts)
    for act in acts:
        encoded = encoder.encode(act)
        decoded = encoder.decode(encoded)
        assert decoded == act