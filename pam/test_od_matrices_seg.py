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
    
    household = Household(hid = '0')
    person = Person(pid='0',  home_area='Barnet', attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Barnet', start_time=0))
    person.add(Leg(1, mode='car', start_area='Barnet', end_area='Southwark', start_time=400, purpose='work'))
    person.add(Activity(2,'work', 'Southwark', start_time=420))
    person.add(Leg(2,'car', start_area='Southwark', end_area='Barnet', start_time=880, purpose='work'))
    person.add(Activity(3,'home','Barnet',start_time=900, end_time=1439))
    household.add(person)  
    population.add(household)

    household = Household(hid = '1')
    person = Person(pid='1', home_area='Ealing', attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Ealing',start_time=0))
    person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Westminster,City of London', start_time=450, purpose='education'))
    person.add(Activity(2,'education', 'Westminster,City of London',start_time=500))
    person.add(Leg(2,'cycle', start_area='Westminster,City of London', end_area='Ealing', start_time=700, purpose='education'))
    person.add(Activity(3,'home','Ealing',start_time=750, end_time=1439))
    household.add(person)  
    population.add(household)

    household = Household(hid = '2')
    person = Person(pid='2', home_area='Ealing',attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Ealing', start_time=0))
    person.add(Leg(1, mode='car', start_area='Ealing', end_area='Westminster,City of London', start_time=450, purpose='work'))
    person.add(Activity(2,'work', 'Westminster,City of London',start_time=480))
    person.add(Leg(2,'car', start_area='Westminster,City of London', end_area='Ealing', start_time=880, purpose='work'))
    person.add(Activity(3,'home','Ealing',start_time=900, end_time=1439))
    household.add(person)  
    population.add(household)

    household = Household(hid = '3')
    person = Person(pid='3', home_area='Barnet',attributes = {'occ':'blue'})
    person.add(Activity(1, 'home','Barnet', start_time = 0))
    person.add(Leg(1, mode='walk', start_area='Barnet', end_area='Barnet', start_time=450, purpose='shop'))
    person.add(Activity(2,'shop', 'Barnet',start_time=470))
    person.add(Leg(2,'walk', start_area='Barnet', end_area='Barnet', start_time=600, purpose='shop'))
    person.add(Activity(3,'home','Barnet',start_time=620, end_time=1439))
    household.add(person)  
    population.add(household)

    household = Household(hid = '4')
    person = Person(pid='4', home_area='Ealing',attributes = {'occ':'blue'})
    person.add(Activity(1, 'home','Ealing', start_time = 0))
    person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Ealing', start_time=400, purpose='work'))
    person.add(Activity(2,'work', 'Ealing',start_time=420))
    person.add(Leg(2,'cycle', start_area='Ealing', end_area='Ealing', start_time=880, purpose='work'))
    person.add(Activity(3,'home','Ealing',start_time=900, end_time=1439))
    household.add(person)  
    population.add(household)

    od_matrix_file = os.path.join(tmpdir, "od_matrix_seg_test.csv")

    od_seg(population, od_matrix_file, mode_seg='car') 

    od_matrix_csv_string = open(od_matrix_file).read()

    assert od_matrix_csv_string =='ozone,Barnet,Ealing,Southwark,"Westminster,City of London"\nBarnet,0,0,1,0\nEaling,0,0,0,1\nSouthwark,1,0,0,0\n"Westminster,City of London",0,1,0,0\n'