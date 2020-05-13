import pandas as pd
import os
from pam.activity import Activity, Leg
from pam.core import Population, Household, Person
from pam.od_matrices import extract_od_seg

def test_writes_od_matrix_seg_to_expected_file(tmpdir):
    population = Population()
    for hid in range(1, 11):
        household = Household(hid)
        population.add(household)

        for pid in range (2):
            person = Person(pid)
            person.add(Activity(1,'home', 'Barnet'))
            person.add(Leg(1, mode='car', start_area='Barnet', end_area='Southwark', start_time='08:00:00', purpose='work'))
            person.add(Activity(2,'work', 'Southwark'))
            person.add(Leg(2,'car', start_area='Southwark', end_area='Barnet', start_time='17:30:00', purpose='work'))
            person.add(Activity(3,'work', 'Barnet'))
            household.add(person)

    od_matrix_file = os.path.join(tmpdir, "od_matrix_test.csv")

    extract_od_seg(population, od_matrix_file, mode_seg='car',purp_seg='work') # would i be able to test both filter?

    od_matrix_csv_string = open(od_matrix_file).read()
    assert od_matrix_csv_string == 'ozone,Barnet,Southwark\nBarnet,0,20\nSouthwark,20,0\n' 
        # change this to be meaningful
        # maybe change the pop sample too to be variant a few different modes and then how many od do i expect
    