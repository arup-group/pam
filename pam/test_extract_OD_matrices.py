import pytest
import os
import pandas as pd
from pam.activity import Plan, Activity, Leg
from pam.core import Population, Household, Person
from pam.extract_OD_matrices import extract_od

def test_extract_od():
    population = Population()
    for hid in range(1,11):
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

    assert extract_od(population, path=os.path.join(r'C:\Users\Iseul.Song\PythonProjects', 'OD_matrix_test.csv'))



    # if __name__ == "__main__":
    #     test_extract_od()
    ### why the line 27 and 28 don't seem to work? 