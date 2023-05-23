"""
Manages zone-level data required by the planner module.
"""

import pandas as pd
import numpy as np

class Zones:
    def __init__(
        self,
        data: pd.DataFrame
    ) -> None:
        """
        :param data: A dataframe with variables as columns and the zone as index
        """
        self.data = data

    def __getattr__(self, __name: str) -> np.array:
        return self.data[__name].values
    
    def __getitem__(self, __name: str) -> np.array:
        return self.__getattr__(__name)
    
    def __repr__(self) -> str:
        r = 'Attraction data\n'
        r += repr(self.data)
        return r
