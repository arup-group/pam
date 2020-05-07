import pytest
import pandas as pd

import pam.plot as plot
from .fixtures import person_heh


def test_build_person_dataframe(person_heh):
    df = plot.build_person_df(person_heh)
    assert len(df) == 5
    assert list(df.act) == ['Home', 'Travel', 'Education', 'Travel', 'Home']


def test_build_cmap_dict():
    df = pd.DataFrame(
        [
            {'act':'Home', 'dur':None},
            {'act':'Travel', 'dur':None},
            {'act':'Work', 'dur':None},
            {'act':'Travel', 'dur':None},
            {'act':'Home', 'dur':None},
        ]
    )
    cmap = plot.build_cmap(df)
    assert isinstance(cmap, dict)
    assert set(list(cmap)) == set(['Home', 'Work', 'Travel'])
    