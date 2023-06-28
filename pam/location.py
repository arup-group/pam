class Location:
    def __init__(self, loc=None, link=None, area=None):
        self.loc = loc
        self.link = link
        self.area = area

    @property
    def x(self):
        if self.loc:
            return self.loc.x
        return None

    @property
    def y(self):
        if self.loc:
            return self.loc.y
        return None

    @property
    def min(self):
        if self.loc is not None:
            return self.loc
        if self.link is not None:
            return self.link
        if self.area is not None:
            return self.area

    @property
    def max(self):
        if self.area is not None:
            return self.area
        if self.link is not None:
            return self.link
        if self.loc is not None:
            return self.loc

    @property
    def exists(self):
        if self.area or self.link or self.loc:
            return True

    def __str__(self):
        return str(self.min)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.area == other
        if self.loc is not None and other.loc is not None:
            return self.loc == other.loc
        if self.link is not None and other.link is not None:
            return self.link == other.link
        if self.area is not None and other.area is not None:
            return self.area == other.area
        raise UserWarning(
            "Cannot check for location equality without same loc types (areas/locs/links)."
        )

    def copy(self):
        return Location(loc=self.loc, link=self.link, area=self.area)
