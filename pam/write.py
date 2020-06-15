import os
from datetime import datetime
import pandas as pd
from lxml import etree as et

from .activity import Activity, Leg
from .utils import datetime_to_matsim_time as dttm
from .utils import timedelta_to_matsim_time as tdtm
from .utils import minutes_to_datetime as mtdt
from .utils import write_xml


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
                    'seq': seq,
                    'purp': leg.purp,
                    'mode': leg.mode,
                    'tst': leg.start_time.time(),  # todo convert to min
                    'tet': leg.end_time.time(),  # todo convert to min
                    'freq': person.freq,
                }
            )
    pd.DataFrame(record).to_csv(path)

    if attributes_path:
        record = []
        for hid, pid, person in population.people():
            line = person.attributes
            line['hid'] = hid
            line['pid'] = pid
            record.append(line)
        pd.DataFrame(record).to_csv(attributes_path)


def write_od_matrices(
        population, 
        path, 
        leg_filter=None, 
        person_filter=None, 
        time_minutes_filter=None):

    """
	Write a core population object to tabular O-D weighted matrices.
	Optionally segment matrices by leg attributes(mode/ purpose), person attributes or specific time periods.
    A single filter can be applied each time.
	:param population: core.Population
    :param path: directory to write OD matrix files
    :param leg_filter: select between 'Mode', 'Purpose'
    :param person_filter: select between given attribute categories (column names) from person attribute data
    :param time_minutes_filter: a list of tuples to slice times, 
    e.g. [(start_of_slicer_1, end_of_slicer_1), (start_of_slicer_2, end_of_slicer_2), ... ]
	:return: None
	"""

    legs = []      
    
    for hid, household in population.households.items():
        for pid, person in household.people.items():
            for leg in person.legs:
                data = {'Household ID': hid,
                            'Person ID': pid,
                            'Origin':leg.start_location.area,
                            'Destination': leg.end_location.area,
                            'Purpose': leg.purp,
                            'Mode': leg.mode,
                            'Sequence': leg.seq,
                            'Start time': leg.start_time,
                            'End time': leg.end_time}                
                if person_filter:
                    legs.append({**data, **person.attributes})
                else:
                    legs.append(data)         
        
    df_total = pd.DataFrame(data=legs, columns = ['Origin','Destination']).set_index('Origin')              
    matrix = df_total.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
    matrix.to_csv(os.path.join(path, 'total_od.csv'))

    data_legs = pd.DataFrame(data=legs)
    
    if leg_filter:
        data_legs_grouped=data_legs.groupby(leg_filter)
        for filter, leg in data_legs_grouped:
            df = pd.DataFrame(data=leg, columns = ['Origin','Destination']).set_index('Origin')
            matrix = df.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
            matrix.to_csv(os.path.join(path, filter+'_od.csv'))
        return None

    elif person_filter:
        data_legs_grouped=data_legs.groupby(person_filter)              
        for filter, leg in data_legs_grouped:
            df = pd.DataFrame(data=leg, columns = ['Origin','Destination']).set_index('Origin')
            matrix = df.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
            matrix.to_csv(os.path.join(path, filter+'_od.csv'))
        return None
        
    elif time_minutes_filter:
        periods = []
        for time in time_minutes_filter:
            periods.append(time)               
        for start_time, end_time in periods:
            file_name = str(start_time) +'_to_'+ str(end_time)
            start_time = mtdt(start_time)
            end_time = mtdt(end_time)
            data_time = data_legs[(data_legs['Start time']>= start_time)&(data_legs['Start time']< end_time)]
            df = pd.DataFrame(data=data_time, columns = ['Origin','Destination']).set_index('Origin')        
            matrix = df.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
            matrix.to_csv(os.path.join(path, 'time_'+file_name+'_od.csv'))
        return None        


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
                        'x': str(float(component.location.loc.x)),
                        'y': str(float(component.location.loc.y)),
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
                'x': str(float(component.location.loc.x)),
                'y': str(float(component.location.loc.y)),
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


def write_population_csv(list_of_populations, export_path):
    """"
    This function creates csv export files of populations, households, people, legs and actvities. 
    This export could be used to share data outside of Python or build an interactive dashboard.
    """
    populations = []
    households = []
    people = []
    legs = []
    activities = []

    for idx, population in enumerate(list_of_populations):
        populations.append(
            {
                'Scenario ID': idx,
                'Scenario name': population.name
            })
        file_path = os.path.join(export_path, 'populations.csv')
        pd.DataFrame(populations).to_csv(file_path, index=False)

        for hid, hh in population.households.items():
            households.append({
                'Scenario ID': idx,
                'Household ID': hid,
                'Area': hh.area,
                'Scenario_Household_ID': str(idx) + str("_") + str(hid)
            })
        file_path = os.path.join(export_path, 'households.csv')
        pd.DataFrame(households).to_csv(file_path, index=False)

        for hid, pid, person in population.people():
            d_to_append = {
                'Scenario_Household_ID': str(idx) + str("_") + str(hid),
                'Scenario_Person_ID': str(idx) + str("_") + str(pid),
                'Scenario ID': idx,
                'Household ID': hid,
                'Person ID': pid
            }
            people.append({**d_to_append, **person.attributes})
        file_path = os.path.join(export_path, 'people.csv')
        pd.DataFrame(people).to_csv(file_path, index=False)

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
                    'Duration': str(leg.duration)
                })
        file_path = os.path.join(export_path, 'legs.csv')
        pd.DataFrame(legs).to_csv(file_path, index=False)

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
                    'Duration': str(activity.duration)
                })
        file_path = os.path.join(export_path, 'activities.csv')
        pd.DataFrame(activities).to_csv(file_path, index=False)
