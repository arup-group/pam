import pandas as pd
import os
from pam.activity import Activity, Leg
from pam.core import Population, Household, Person
from pam.od_matrices import extract_od_seg

def test_writes_od_matrix_seg_to_expected_file(tmpdir):
    population = Population()
    for hid in range(5):
        household = Household(hid)
        population.add(household)

    person0 = Person(1, attributes = 'white', home_area='Barnet')
    person0.add(Activity(1, 'home','Barnet'))
    person0.add(Leg(1, mode='car', start_area='Barnet', end_area='Southwark', start_time='08:00:00', purpose='work'))
    person0.add(Activity(2,'work', 'Southwark'))
    person0.add(Leg(2,'car', start_area='Southwark', end_area='Barnet', start_time='17:30:00', purpose='work'))
    person0.add(Activity(3,'home','Barnet'))
    household[0].add(person0)

    person1 = Person(1, attributes = 'white', home_area='Ealing')
    person1.add(Activity(1, 'home','Ealing'))
    person1.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Westminster,City of London', start_time='08:00:00', purpose='education'))
    person1.add(Activity(2,'education', 'Westminster,City of London'))
    person1.add(Leg(2,'cycle', start_area='Westminster,City of London', end_area='Ealing', start_time='14:00:00', purpose='education'))
    person1.add(Activity(3,'home','Ealing'))
    household[1].add(person1)

    person2 = Person(1, attributes = 'white', home_area='Ealing')
    person2.add(Activity(1, 'home','Ealing'))
    person2.add(Leg(1, mode='car', start_area='Ealing', end_area='Westminster,City of London', start_time='07:30:00', purpose='work'))
    person2.add(Activity(2,'work', 'Westminster,City of London'))
    person2.add(Leg(2,'car', start_area='Westminster,City of London', end_area='Ealing', start_time='17:30:00', purpose='work'))
    person2.add(Activity(3,'home','Ealing'))
    household[2].add(person2)

    person3 = Person(1, attributes = 'blue', home_area='Barnet')
    person3.add(Activity(1, 'home','Barnet'))
    person3.add(Leg(1, mode='walk', start_area='Barnet', end_area='Barnet', start_time='08:00:00', purpose='shop'))
    person3.add(Activity(2,'shop', 'Barnet'))
    person3.add(Leg(2,'walk', start_area='Barnet', end_area='Barnet', start_time='09:00:00', purpose='shop'))
    person3.add(Activity(3,'home','Barnet'))
    household[3].add(person3)

    person4 = Person(1, attributes = 'blue', home_area='Ealing')
    person4.add(Activity(1, 'home','Ealing'))
    person4.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Ealing', start_time='07:30:00', purpose='work'))
    person4.add(Activity(2,'work', 'Ealing'))
    person4.add(Leg(2,'cycle', start_area='Ealing', end_area='Ealing', start_time='17:30:00', purpose='work'))
    person4.add(Activity(3,'home','Ealing'))
    household[4].add(person4)
    
    od_matrix_file = os.path.join(tmpdir, "od_matrix_seg_test.csv")

    extract_od_seg(population, od_matrix_file, mode_seg='car',purp_seg='work') # would i be able to test both filter?

    od_matrix_csv_string = open(od_matrix_file).read()
    assert od_matrix_csv_string == 'ozone,Barnet,Southwark\nBarnet,0,20\nSouthwark,20,0\n' 
        # change this to be meaningful

    