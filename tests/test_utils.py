from s2sphere import CellId
from shapely.geometry import LineString, Point
from pam import utils
from pam import plot
from pam.core import Household, Population
from tests.fixtures import Hilda, Steve, instantiate_household_with


def test_build_person_geodataframe(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = Steve.build_travel_geodataframe()
    geometry = gdf['geometry'].to_list()
    assert geometry == [LineString([Point(1, 2), Point(2, 3)]) for leg in Steve.legs]
    assert 'pid' in gdf.columns


def test_build_hhld_geodataframe(Steve, Hilda):
    hhld = instantiate_household_with([Steve, Hilda])
    for pid, person in hhld:
        for leg in person.legs:
            leg.start_location.loc = Point(1, 2)
            leg.end_location.loc = Point(2, 3)
    gdf = hhld.build_travel_geodataframe()
    for idx in gdf.index:
        assert isinstance(gdf.loc[idx, 'geometry'], LineString)
    geometry = gdf['geometry'].to_list()
    assert geometry == [LineString([Point(1, 2), Point(2, 3)]) for i in range(9)]
    assert 'pid' in gdf.columns
    assert 'hid' in gdf.columns


def test_build_pop_geodataframe(Steve, Hilda):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    for leg in Hilda.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    pop = Population()
    pop.add(instantiate_household_with([Steve, Hilda], hid=1))
    pop.add(instantiate_household_with([Hilda], hid=2))
    pop.add(instantiate_household_with([Steve], hid=3))

    gdf = pop.build_travel_geodataframe()
    for idx in gdf.index:
        assert isinstance(gdf.loc[idx, 'geometry'], LineString)
    geometry = gdf['geometry'].to_list()
    assert geometry == [LineString([Point(1, 2), Point(2, 3)]) for i in range(18)]
    assert 'pid' in gdf.columns
    assert 'hid' in gdf.columns


def test_get_linestring_with_s2_cellids():
    from_point = CellId(5221390681063996525)
    to_point = CellId(5221390693823388667)

    ls = utils.get_linestring(from_point, to_point)
    assert isinstance(ls, LineString)
    assert [(round(c[0], 6), round(c[1], 6)) for c in ls.coords] == [(-0.137925, 51.521699), (-0.134456, 51.520027)]
