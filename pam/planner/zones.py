"""
Manages zone-level data required by the planner module.
"""


class Zones:
    def __init__(
        self,
        data
    ) -> None:
        """
        :param data: A dataframe with variables as columns and the zone as index
        """
        self.data = data
