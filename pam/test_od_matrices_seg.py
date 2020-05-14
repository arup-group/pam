import pandas as pd
import os
from pam.activity import Activity, Leg
from pam.core import Population, Household, Person
from pam.od_matrices_seg import od_seg 
from pam.variables import END_OF_DAY

import csv
import os
import pytest


def test_writes_od_matrix_seg_to_expected_file(tmpdir):
    population = Population()

    for pid in range(6):
        person = Person(pid)
        household = Household(pid) # pid == hid
        household.add(person)        
        population.add(household)

    print(household)
    
    if person.pid == '0':
        person = Person(pid='0', attributes = 'white', home_area='Barnet')
        person.add(Activity(1, 'home','Barnet'))
        person.add(Leg(1, mode='car', start_area='Barnet', end_area='Southwark', start_time='08:00:00', purpose='work'))
        person.add(Activity(2,'work', 'Southwark'))
        person.add(Leg(2,'car', start_area='Southwark', end_area='Barnet', start_time='17:30:00', purpose='work'))
        person.add(Activity(3,'home','Barnet'))

    if person.pid == '1':
        person = Person(pid='1', attributes = 'white', home_area='Ealing')
        person.add(Activity(1, 'home','Ealing'))
        person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Westminster,City of London', start_time='08:00:00', purpose='education'))
        person.add(Activity(2,'education', 'Westminster,City of London'))
        person.add(Leg(2,'cycle', start_area='Westminster,City of London', end_area='Ealing', start_time='14:00:00', purpose='education'))
        person.add(Activity(3,'home','Ealing'))

    if person.pid == '2':
        person = Person(pid='2', attributes = 'white', home_area='Ealing')
        person.add(Activity(1, 'home','Ealing'))
        person.add(Leg(1, mode='car', start_area='Ealing', end_area='Westminster,City of London', start_time='07:30:00', purpose='work'))
        person.add(Activity(2,'work', 'Westminster,City of London'))
        person.add(Leg(2,'car', start_area='Westminster,City of London', end_area='Ealing', start_time='17:30:00', purpose='work'))
        person.add(Activity(3,'home','Ealing'))

    if person.pid == '3':
        person = Person(pid='3', attributes = 'blue', home_area='Barnet')
        person.add(Activity(1, 'home','Barnet'))
        person.add(Leg(1, mode='walk', start_area='Barnet', end_area='Barnet', start_time='08:00:00', purpose='shop'))
        person.add(Activity(2,'shop', 'Barnet'))
        person.add(Leg(2,'walk', start_area='Barnet', end_area='Barnet', start_time='09:00:00', purpose='shop'))
        person.add(Activity(3,'home','Barnet'))

    if person.pid == '4':
        person = Person(pid='4', attributes = 'blue', home_area='Ealing')
        person.add(Activity(1, 'home','Ealing'))
        person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Ealing', start_time='07:30:00', purpose='work'))
        person.add(Activity(2,'work', 'Ealing'))
        person.add(Leg(2,'cycle', start_area='Ealing', end_area='Ealing', start_time='17:30:00', purpose='work'))
        person.add(Activity(3,'home','Ealing'))
    
    od_matrix_file = os.path.join(tmpdir, "od_matrix_seg_test.csv")

    extract_od_seg(population, od_matrix_file, mode_seg='car',purp_seg='work') 

    od_matrix_csv_string = open(od_matrix_file).read()
    assert od_matrix_csv_string == 'ozone,Barnet,Southwark,Ealing,Westminster,City of London,\nBarnet,0,20\nSouthwark,20,0\nEaling,,\nWestminster,City of London,,\n' 
        # would i be able to test both filter?
        # sort time 

test_writes_od_matrix_seg_to_expected_file('/Users/Iseul.Song/PythonProjects/IS_WIP')    