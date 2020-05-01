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
    populations = []
    households = []
    people = []
    legs = []
    activities = []
    locations = []
    
    for idx, population in enumerate(list_of_populations):

        #Population csv
        populations.append(
            {
                'Scenario ID': idx,
                'Scenario name': population.name   
            })

        pathfilename = os.path.join(export_path, 'populations.csv')
        pd.DataFrame(populations).to_csv(pathfilename, index = False)

        #Household df
        
        for hid, hh in population.households.items():
            households.append({
                'Scenario ID': idx,
                'Household ID': hid,
                'Area': hh.area,
                'Scenario_Household_ID': str(idx) + str("_") + str(hid)

            })
              
        pathfilename = os.path.join(export_path, 'households.csv')
        pd.DataFrame(households).to_csv(pathfilename, index = False)


        #People csv
        
        for hid, pid, person in population.people():
            d_to_append = {
                'Scenario_Household_ID': str(idx) + str("_") + str(hid),
                'Scenario_Person_ID': str(idx) + str("_") + str(pid),
                'Scenario ID': idx,
                'Household ID': hid,
                'Person ID': pid
            }            
            people.append({**d_to_append, **person.attributes}) 

        pathfilename = os.path.join(export_path, 'people.csv')
        pd.DataFrame(people).to_csv(pathfilename, index = False)
        

        #Leg csv
        
        for hid, pid, person in population.people():
            for seq, leg in enumerate(person.legs):
                legs.append({
                    'Scenario_Person_ID': str(idx) + str("_") + str(pid),
                    'Scenario ID': idx,
                    'Household ID': hid,
                    'Person ID': pid,
                    'Origin': leg.start_location.area,
                    'Destination': leg.end_location.area,
                    'Purpose': leg.act,  
                    'Mode': leg.mode,
                    'Sequence': leg.seq,
                    'Start time': leg.start_time,  
                    'End time': leg.end_time, 
                    'Duration': leg.duration
                 
            })

        pathfilename = os.path.join(export_path, 'legs.csv')
        pd.DataFrame(legs).to_csv(pathfilename, index = False)

        #Activity csv
        
        for hid, pid, person in population.people():
            for seq, activity in enumerate(person.activities):
                activities.append({
                    'Scenario_Person_ID': str(idx) + str("_") + str(pid),
                    'Scenario ID': idx,
                    'Household ID': hid,
                    'Person ID': pid,
                    'Location': activity.location.area,
                    'Purpose': activity.act,  
                    'Sequence': activity.seq,
                    'Start time': activity.start_time,  
                    'End time': activity.end_time,  
                    'Duration': activity.duration
            })

        pathfilename = os.path.join(export_path, 'activities.csv')
        pd.DataFrame(activities).to_csv(pathfilename, index = False)
               
    return 