import os

from pam.activity import Activity, Leg
from pam.core import Population, Household, Person
from pam.od_matrices import extract_od


def test_writes_od_matrix_to_expected_file(tmpdir):
    population = Population()
    for hid in range(1, 11):
        household = Household(hid)
        population.add(household)

        for pid in range (2):
            person = Person(pid)
            person.add(Activity(1,'home', 'Barnet'))
            person.add(Leg(1,'car', start_area='Barnet', end_area='Southwark'))
            person.add(Activity(2,'work', 'Southwark'))
            person.add(Leg(2,'car', start_area='Southwark', end_area='Barnet'))
            person.add(Activity(3,'work', 'Barnet'))
            household.add(person)

    od_matrix_file = os.path.join(tmpdir, "od_matrix_test.csv")

    extract_od(population, od_matrix_file)

    od_matrix_csv_string = open(od_matrix_file).read()
    assert od_matrix_csv_string == 'ozone,Barnet,Southwark\nBarnet,0,20\nSouthwark,20,0\n'
