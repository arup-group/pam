from datetime import datetime, timedelta
from lxml import etree as et
import os
import gzip
import pandas as pd

from .core import Population, Household, Person
from .activity import Plan, Activity, Leg
from .utils import minutes_to_datetime as mtdt
from .utils import datetime_to_matsim_time as dttm
from .utils import timedelta_to_matsim_time as tdtm
from .utils import get_elems, write_xml


def write_travel_diary(population, path, attributes_path=None):
	"""
	Write a core population object to the standard population tabular formats.
	Only write attributes if given attributes_path.
	:param population: core.Population
	:return: None
	"""
	record = []
	for hid, pid, person in population.people():
		for seq, leg in enumerate(person.legs):
			record.append(
				{
					'pid': pid,
					'hid': hid,
					'hzone': person.home,
					'ozone': leg.start_location.area,
					'dzone': leg.end_location.area,
					'purp': person.plan[seq+1],  # todo this is not the same as the parse logic!!!
					'mode': leg.mode,
					'tst': leg.start_time,  # todo convert to min
					'tet': leg.end_time,  # todo convert to min
					'freq': person.freq,
				}
			)
	pd.DataFrame(record).to_csv(path)

	if attributes_path:
		record = []
		for hid, pid, person in population.people():
			record.append(person.attributes)
		pd.DataFrame(record).to_csv(attributes_path)


def write_od_matrices(population, type_seg=None, mode_seg=None, time_seg=None):
	"""
	Write a core population object to tabular O-D weighted matrices.
	Optionally segment matrices by type of journey (most likelly based on occupation),
	mode and/or time (ie peaks).
	:param population: core.Population
	:param type_seg: segmentation option tbc
	:param mode_seg: segmentation option tbc
	:param time_seg: segmentation option tbc
	:return: None
	"""
	# todo
	raise NotImplementedError


def write_matsim(
	population,
	plans_path,
	attributes_path,
	comment=None,
	household_key=None
	):
	"""
	Write a core population object to matsim xml formats.
	Note that this requires activity locs to be set (shapely.geomerty.Point).
	Comment string is optional.
	Set household_key of you wish to add household id to attributes.
	:param population: core.Population
	:return: None
	"""
	# note - these are written sequentially to reduce RAM required...
	write_matsim_plans(population, plans_path, comment)
	write_matsim_attributes(population, attributes_path, comment, household_key=household_key)


def write_matsim_plans(population, location, comment=None):

	# todo write this incrementally to save memory: https://lxml.de/api.html#incremental-xml-generation

	population_xml = et.Element('population')

	# Add some useful comments
	if comment:
		population_xml.append(et.Comment(comment))
	population_xml.append(et.Comment(f"Created {datetime.today()}"))

	for _, household in population:
		for pid, person in household:
			person_xml = et.SubElement(population_xml, 'person', {'id': str(pid)})
			plan_xml = et.SubElement(person_xml, 'plan', {'selected': 'yes'})
			for component in person[:-1]:
				if isinstance(component, Activity):
					et.SubElement(plan_xml, 'act', {
						'type': component.act,
						'x': str(int(component.location.loc.x)),
						'y': str(int(component.location.loc.y)),
						'end_time': dttm(component.end_time)
					}
				)
				if isinstance(component, Leg):
					et.SubElement(plan_xml, 'leg', {
						'mode': component.mode,
						'trav_time': tdtm(component.duration)})

			component = person[-1]  # write the last activity without an end time
			et.SubElement(plan_xml, 'act', {
						'type': component.act,
						'x': str(int(component.location.loc.x)),
						'y': str(int(component.location.loc.y)),
					}
				)

	write_xml(population_xml, location, matsim_DOCTYPE='population', matsim_filename='population_v5')
	# todo assuming v5?


def write_matsim_attributes(population, location, comment=None, household_key=None):
	
	attributes_xml = et.Element('objectAttributes')  # start forming xml

	# Add some useful comments
	if comment:
		attributes_xml.append(et.Comment(comment))
	attributes_xml.append(et.Comment(f"Created {datetime.today()}"))

	for hid, household in population:
		for pid, person in household:
			person_xml = et.SubElement(attributes_xml, 'object', {'id': str(pid)})

			attributes = person.attributes
			if household_key:  # add hid to household_key if using household key
				attributes[household_key] = hid

			for k, v in attributes.items():
				attribute_xml = et.SubElement(person_xml, 'attribute', {'class': 'java.lang.String', 'name': str(k)})
				attribute_xml.text = str(v)
			

	write_xml(attributes_xml, location, matsim_DOCTYPE='objectAttributes', matsim_filename='objectattributes_v1')
	# todo assuming v1?

def create_population_export(list_of_populations, export_path):
    
    """"
    This function creates csv export files of populations, households, people, legs and actvities. 
    This export could be used to share data outside of Python or build an interactive dashboard.
    """
    populations = []
    households = []
    people = []
    legs = []
    activities = []
    locations = []
    
    for population in list_of_populations:

        """
        Create population export
        """
        populations.append(
            {
                'Scenario ID': id(population),
                'Scenario name': population.name   
            })

        pathfilename = export_path+str('/populations.csv')
        populations_df = pd.DataFrame(populations)
        pd.DataFrame(populations).to_csv(pathfilename, index = False)

        """
        Create household export
        """
        
        for hid in population.households:
            households.append({
                'Scenario ID': id(population),
                'Household ID': hid,
                'Area': household.area,
                'Scenario_Household_ID': str(id(population)) + str("_") + str(hid)

            })
        households_df = pd.DataFrame(households)
        pathfilename = export_path+str('/households.csv')
        pd.DataFrame(households).to_csv(pathfilename, index = False)


        """
        Create people export
        """
        
        for hid, pid, person in population.people():
            d_to_append = {
                'Scenario_Household_ID': str(id(population)) + str("_") + str(hid),
                'Scenario_Person_ID': str(id(population)) + str("_") + str(pid),
                'Scenario ID': id(population),
                'Household ID': hid,
                'Person ID': pid
            }            
            people.append({**d_to_append, **person.attributes}) 


        people_df = pd.DataFrame(people)
        pathfilename = export_path+str('/people.csv')
        pd.DataFrame(people).to_csv(pathfilename, index = False)
 

        """
        Create legs export
        """
                
        for hid, pid, person in population.people():
            for seq, leg in enumerate(person.legs):
                legs.append({
                    'Scenario_Person_ID': str(id(population)) + str("_") + str(pid),
                    'Scenario ID': id(population),
                    'Household ID': hid,
                    'Person ID': pid,
                    'Origin': leg.start_location.area,
                    'Destination': leg.end_location.area,
                    'Purpose': leg.act,  
                    'Mode': leg.mode,
                    'Sequence': leg.seq,
                    'Start time': leg.start_time,  
                    'End time': leg.end_time, 
                    'Duration': leg.end_time - leg.start_time
                 
            })

        legs_df = pd.DataFrame(legs)
        pathfilename = export_path+str('/legs.csv')
        pd.DataFrame(legs).to_csv(pathfilename, index = False)

        """
        Create activities export
        """
                
        for hid, pid, person in population.people():
            for seq, activity in enumerate(person.activities):
                activities.append({
                    'Scenario_Person_ID': str(id(population)) + str("_") + str(pid),
                    'Scenario ID': id(population),
                    'Household ID': hid,
                    'Person ID': pid,
                    'Location': activity.location.area,
                    'Purpose': activity.act,  
                    'Sequence': activity.seq,
                    'Start time': activity.start_time,  
                    'End time': activity.end_time,  
                    'Duration': activity.end_time - activity.start_time
            })

        activities_df = pd.DataFrame(activities)
        pathfilename = export_path+str('/activities.csv')
        pd.DataFrame(activities).to_csv(pathfilename, index = False)
        
        
    return 