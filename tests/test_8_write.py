import csv
import os
import pytest

from datetime import datetime

from .fixtures import population_heh
from pam.activity import Activity, Leg
from pam.core import Household, Person, Population
from pam.write import write_travel_diary, \
    write_population_csv, write_matsim_plans, write_matsim_attributes, write_od_matrices
from pam.read import read_matsim


def test_write_plans_xml(tmp_path, population_heh):
    location = str(tmp_path / "test.xml")
    write_matsim_plans(population_heh, location=location, comment="test")
    # TODO make assertions about the content of the created file


def test_write_plans_gzip(tmp_path, population_heh):
    location = str(tmp_path / "test.xml.gz")
    write_matsim_plans(population_heh, location=location, comment="test")

    expected_file = "{}/test.xml.gz".format(tmp_path)
    assert os.path.exists(expected_file)
    # TODO make assertions about the content of the created file


def test_write_attributes_xml(tmp_path, population_heh):
    location = str(tmp_path / "test.xml")
    write_matsim_attributes(population_heh, location=location, comment="test")

    expected_file = "{}/test.xml".format(tmp_path)
    assert os.path.exists(expected_file)
    # TODO make assertions about the content of the created file


def test_write_attributes_gzip(tmp_path, population_heh):
    location = str(tmp_path / "test.xml.gz")
    write_matsim_attributes(population_heh, location=location, comment="test")

    expected_file = "{}/test.xml.gz".format(tmp_path)
    assert os.path.exists(expected_file)
    # TODO make assertions about the content of the created file


def test_write_read_continuity_xml(tmp_path, population_heh):
    plans_location = str(tmp_path / "test_plans.xml")
    write_matsim_plans(population_heh, location=plans_location, comment="test")
    attributes_location = str(tmp_path / "test_attributes.xml")
    write_matsim_attributes(population_heh, location=attributes_location, comment="test")
    population = read_matsim(
        plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
    )
    assert population_heh['0']['1'].plan == population['0']['1'].plan


def test_write_read_continuity_gzip(tmp_path, population_heh):
    plans_location = str(tmp_path / "test_plans.xml.gz")
    write_matsim_plans(population_heh, location=plans_location, comment="test")
    attributes_location = str(tmp_path / "test_attributes.xml.gz")
    write_matsim_attributes(population_heh, location=attributes_location, comment="test")
    population = read_matsim(
        plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
    )
    assert population_heh['0']['1'].plan == population['0']['1'].plan


def test_read_write_read_continuity_complex_xml(tmp_path):
    test_trips_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plans.xml"))
    test_attributes_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        "test_data/test_matsim_attributes.xml"))
    population_in = read_matsim(test_trips_path, test_attributes_path)
    complex_plan_in = population_in['census_1']['census_1'].plan

    plans_location = str(tmp_path / "test_plans.xml")
    write_matsim_plans(population_in, location=plans_location, comment="test")
    attributes_location = str(tmp_path / "test_attributes.xml")
    write_matsim_attributes(population_in, location=attributes_location, comment="test")

    population_out = read_matsim(
        plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
    )
    complex_plan_out = population_out['census_1']['census_1'].plan

    assert complex_plan_in == complex_plan_out


def test_write_travel_plans(tmp_path, population_heh):
    location = str(tmp_path / "test.csv")
    write_travel_diary(population_heh, path=location)

    expected_file = "{}/test.csv".format(tmp_path)
    assert os.path.exists(expected_file)
    # TODO make assertions about the content of the created file


def test_writes_od_matrix_to_expected_file(tmpdir):
    population = Population()
    
    household = Household(hid = '0')
    person = Person(pid='0',  home_area='Barnet', attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Barnet', start_time=mtdt(0)))
    person.add(Leg(1, mode='car', start_area='Barnet', end_area='Southwark', start_time=mtdt(400), purpose='work'))
    person.add(Activity(2,'work', 'Southwark', start_time=mtdt(420)))
    person.add(Leg(2,'car', start_area='Southwark', end_area='Barnet', start_time=mtdt(1020), purpose='work'))
    person.add(Activity(3,'home','Barnet',start_time=mtdt(1040), end_time=mtdt(1439)))
    household.add(person)  
    population.add(household)

    household = Household(hid = '1')
    person = Person(pid='1', home_area='Ealing', attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Ealing',start_time=mtdt(0)))
    person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Westminster,City of London', start_time=mtdt(500), purpose='education'))
    person.add(Activity(2,'education', 'Westminster,City of London',start_time=mtdt(550)))
    person.add(Leg(2,'cycle', start_area='Westminster,City of London', end_area='Ealing', start_time=mtdt(700), purpose='education'))
    person.add(Activity(3,'home','Ealing',start_time=mtdt(750), end_time=mtdt(1439)))
    household.add(person)  
    population.add(household)

    household = Household(hid = '2')
    person = Person(pid='2', home_area='Ealing',attributes = {'occ':'white'})
    person.add(Activity(1, 'home','Ealing', start_time=mtdt(0)))
    person.add(Leg(1, mode='car', start_area='Ealing', end_area='Westminster,City of London', start_time=mtdt(450), purpose='work'))
    person.add(Activity(2,'work', 'Westminster,City of London',start_time=mtdt(480)))
    person.add(Leg(2,'car', start_area='Westminster,City of London', end_area='Ealing', start_time=mtdt(1050), purpose='work'))
    person.add(Activity(3,'home','Ealing',start_time=mtdt(1080), end_time=mtdt(1439)))
    household.add(person)  
    population.add(household)

    household = Household(hid = '3')
    person = Person(pid='3', home_area='Barnet',attributes = {'occ':'blue'})
    person.add(Activity(1, 'home','Barnet', start_time = mtdt(0)))
    person.add(Leg(1, mode='walk', start_area='Barnet', end_area='Barnet', start_time=mtdt(450), purpose='shop'))
    person.add(Activity(2,'shop', 'Barnet',start_time=mtdt(470)))
    person.add(Leg(2,'walk', start_area='Barnet', end_area='Barnet', start_time=mtdt(600), purpose='shop'))
    person.add(Activity(3,'home','Barnet',start_time=mtdt(620), end_time=mtdt(1439)))
    household.add(person)  
    population.add(household)

    household = Household(hid = '4')
    person = Person(pid='4', home_area='Ealing',attributes = {'occ':'blue'})
    person.add(Activity(1, 'home','Ealing', start_time = mtdt(0)))
    person.add(Leg(1, mode='cycle', start_area='Ealing', end_area='Ealing', start_time=mtdt(400), purpose='work'))
    person.add(Activity(2,'work', 'Ealing',start_time=mtdt(420)))
    person.add(Leg(2,'cycle', start_area='Ealing', end_area='Ealing', start_time=mtdt(1030), purpose='work'))
    person.add(Activity(3,'home','Ealing',start_time=mtdt(1050), end_time=mtdt(1439)))
    household.add(person)  
    population.add(household)

    attribute_list = ['white', 'blue', 'total']
    mode_list = ['car', 'cycle','walk', 'total']
    time_slice = [(400, 500), (1020, 1060)]
    
    write_od_matrices(population, tmpdir, leg_filter = 'Mode')   
    for m in mode_list:
        od_matrix_file = os.path.join(tmpdir, m+"_od.csv")
        od_matrix_csv_string = open(od_matrix_file).read()       
        if m == 'car':          
            expected_od_matrix = \
                    'Origin,Barnet,Ealing,Southwark,"Westminster,City of London"\n' \
                    'Barnet,0,0,1,0\n' \
                    'Ealing,0,0,0,1\n' \
                    'Southwark,1,0,0,0\n' \
                    '"Westminster,City of London",0,1,0,0\n'        
            assert od_matrix_csv_string == expected_od_matrix           
        if m == 'cycle':          
            expected_od_matrix = \
                    'Origin,Ealing,"Westminster,City of London"\n' \
                    'Ealing,2,1\n' \
                    '"Westminster,City of London",1,0\n'        
            assert od_matrix_csv_string == expected_od_matrix       
        if m == 'walk':          
            expected_od_matrix = \
                    'Origin,Barnet\n' \
                    'Barnet,2\n'
            assert od_matrix_csv_string == expected_od_matrix           
        if m == 'total':
            expected_od_matrix = \
                    'Origin,Barnet,Ealing,Southwark,"Westminster,City of London"\n' \
                    'Barnet,2,0,1,0\n' \
                    'Ealing,0,2,0,2\n' \
                    'Southwark,1,0,0,0\n' \
                    '"Westminster,City of London",0,2,0,0\n'        
            assert od_matrix_csv_string == expected_od_matrix        
                        
    write_od_matrices(population, tmpdir, person_filter = 'occ')   
    for a in attribute_list:
        od_matrix_file = os.path.join(tmpdir, a+"_od.csv")
        od_matrix_csv_string = open(od_matrix_file).read()      
        if a == 'white':          
            expected_od_matrix = \
                    'Origin,Barnet,Ealing,Southwark,"Westminster,City of London"\n' \
                    'Barnet,0,0,1,0\n' \
                    'Ealing,0,0,0,2\n' \
                    'Southwark,1,0,0,0\n' \
                    '"Westminster,City of London",0,2,0,0\n'        
            assert od_matrix_csv_string == expected_od_matrix          
        if a == 'blue':          
            expected_od_matrix = \
                    'Origin,Barnet,Ealing\n' \
                    'Barnet,2,0\n' \
                    'Ealing,0,2\n'      
            assert od_matrix_csv_string == expected_od_matrix         
        if a == 'total':          
            expected_od_matrix = \
                    'Origin,Barnet,Ealing,Southwark,"Westminster,City of London"\n' \
                    'Barnet,2,0,1,0\n' \
                    'Ealing,0,2,0,2\n' \
                    'Southwark,1,0,0,0\n' \
                    '"Westminster,City of London",0,2,0,0\n'        
            assert od_matrix_csv_string == expected_od_matrix          
         
    write_od_matrices(population, tmpdir, time_minutes_filter = [(400,500),(1020,1060)])   
    for start_time, end_time in time_slice:
        file_name = str(start_time) +'_to_'+ str(end_time)
        od_matrix_file = os.path.join(tmpdir,'time_'+file_name+'_od.csv' )
        od_matrix_csv_string = open(od_matrix_file).read()       
        if (start_time, end_time) == (400, 500):
            expected_od_matrix = \
                    'Origin,Barnet,Ealing,Southwark,"Westminster,City of London"\n' \
                    'Barnet,1,0,1,0\n' \
                    'Ealing,0,1,0,1\n'       
            assert od_matrix_csv_string == expected_od_matrix               
        if (start_time, end_time) == (1020, 1060):
            expected_od_matrix = \
                    'Origin,Barnet,Ealing\n' \
                    'Ealing,0,1\n' \
                    'Southwark,1,0\n' \
                    '"Westminster,City of London",0,1\n'     
            assert od_matrix_csv_string == expected_od_matrix     


def test_writes_population_csv_file_to_expected_location(population_heh, tmpdir):
    write_population_csv([population_heh], tmpdir)

    populations_file = "{}/populations.csv".format(tmpdir)
    assert os.path.exists(populations_file)
    with open(populations_file) as file:
        populations_file_lines = file.readlines()
        assert len(populations_file_lines) == 2
        assert populations_file_lines[0] == 'Scenario ID,Scenario name\n'
        assert populations_file_lines[1] == '0,{}\n'.format(population_heh.name)


def test_writes_households_csv_file_to_expected_location(population_heh, tmpdir):
    write_population_csv([population_heh], tmpdir)

    households_file = "{}/households.csv".format(tmpdir)
    assert os.path.exists(households_file)

    population_id = 0  # fixed at 0 because there is only one population being exported
    with open(households_file) as file:
        households_file_lines = file.readlines()
        assert len(households_file_lines) == population_heh.count(households=True) + 1
        assert households_file_lines[0] == 'Scenario ID,Household ID,Area,Scenario_Household_ID\n'
        row_index = 0
        for hid, hh in population_heh.households.items():
            assert households_file_lines[row_index + 1] == \
                   '{},{},{},{}\n'.format(population_id, hid, hh.area, '{}_{}'.format(population_id, hid))
            row_index += 1


def test_writes_people_csv_file_to_expected_location(population_heh, tmpdir):
    write_population_csv([population_heh], tmpdir)

    people_file = "{}/people.csv".format(tmpdir)
    assert os.path.exists(people_file)
    expected_person_index = 0
    population_id = 0 # fixed at 0 because there is only one population being exported
    people_in_pop = list(population_heh.people())
    with open(people_file) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            expected_hid, expected_pid, expected_person = people_in_pop[expected_person_index]
            assert row['Scenario ID'] == '{}'.format(population_id)
            assert row['Household ID'] == '{}'.format(expected_hid)
            assert row['Person ID'] == '{}'.format(expected_pid)
            assert row['Scenario_Household_ID'] == '{}_{}'.format(population_id, expected_hid)
            assert row['Scenario_Person_ID'] == '{}_{}'.format(population_id, expected_pid)
            for column in get_all_people_attributes(population_heh):
                if expected_person.attributes and column in expected_person.attributes:
                    assert row[column] == str(expected_person.attributes[column])
                else:
                    assert row[column] == ''
            expected_person_index += 1


def test_writes_legs_csv_file_to_expected_location(population_heh, tmpdir):
    write_population_csv([population_heh], tmpdir)

    legs_file = "{}/legs.csv".format(tmpdir)
    assert os.path.exists(legs_file)
    expected_legs = get_ordered_legs(population_heh)
    leg_index = 0
    population_id = 0
    with open(legs_file) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            expected_objects = expected_legs[leg_index]
            expected_hid, expected_pid, expected_person = expected_objects[0]
            expected_leg = expected_objects[1]
            assert row['Scenario_Person_ID'] == '{}_{}'.format(population_id, expected_pid)
            assert row['Scenario ID'] == '{}'.format(population_id)
            assert row['Household ID'] == '{}'.format(expected_hid)
            assert row['Person ID'] == '{}'.format(expected_pid)
            assert row['Origin'] == '{}'.format(expected_leg.start_location.area)
            assert row['Destination'] == '{}'.format(expected_leg.end_location.area)
            assert row['Purpose'] == '{}'.format(expected_leg.act)
            assert row['Mode'] == '{}'.format(expected_leg.mode)
            assert row['Sequence'] == '{}'.format(expected_leg.seq)
            assert row['Start time'] == '{}'.format(expected_leg.start_time)
            assert row['End time'] == '{}'.format(expected_leg.end_time)
            assert row['Duration'] == '{}'.format(expected_leg.duration)
            leg_index += 1


def test_writes_activities_csv_file_to_expected_location(population_heh, tmpdir):
    write_population_csv([population_heh], tmpdir)

    activities_file = "{}/activities.csv".format(tmpdir)
    assert os.path.exists(activities_file)
    expected_activities = get_ordered_activities(population_heh)
    activity_index = 0
    population_id = 0
    with open(activities_file) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            expected_objects = expected_activities[activity_index]
            expected_hid, expected_pid, expected_person = expected_objects[0]
            expected_activity = expected_objects[1]
            assert row['Scenario_Person_ID'] == '{}_{}'.format(population_id, expected_pid)
            assert row['Scenario ID'] == '{}'.format(population_id)
            assert row['Household ID'] == '{}'.format(expected_hid)
            assert row['Person ID'] == '{}'.format(expected_pid)
            assert row['Location'] == '{}'.format(expected_activity.location.area)
            assert row['Purpose'] == '{}'.format(expected_activity.act)
            assert row['Sequence'] == '{}'.format(expected_activity.seq)
            assert row['Start time'] == '{}'.format(expected_activity.start_time)
            assert row['End time'] == '{}'.format(expected_activity.end_time)
            assert row['Duration'] == '{}'.format(expected_activity.duration)
            activity_index += 1


###########################################################
# helper functions
###########################################################
def get_all_people_attributes(population):
    attribute_names = set()
    for hid, pid, person in population.people():
        if person.attributes:
            for attribute_name in person.attributes.keys():
                attribute_names.add(attribute_name)
    return attribute_names


def get_ordered_legs(population_heh):
    all_legs = []
    for hid, pid, person in population_heh.people():
        for leg in list(person.legs):
            all_legs.append(((hid, pid, person), leg))
    return all_legs


def get_ordered_activities(population_heh):
    all_activities = []
    for hid, pid, person in population_heh.people():
        for activity in list(person.activities):
            all_activities.append(((hid, pid, person), activity))
    return all_activities
