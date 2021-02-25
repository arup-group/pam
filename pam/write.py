import os
from datetime import datetime
import lxml
import pandas as pd
import geopandas as gp
from lxml import etree as et
from shapely.geometry import Point, LineString
from typing import Tuple, Union, Optional, Callable, List

from .activity import Activity, Leg
from .utils import datetime_to_matsim_time as dttm
from .utils import timedelta_to_matsim_time as tdtm
from .utils import minutes_to_datetime as mtdt
from .utils import write_xml, create_local_dir


def write_travel_diary(
    population,
    plans_path : str,
    attributes_path : Optional[str] = None
    ) -> None:
    """
	Write a core population object to the standard population tabular formats.
	Only write attributes if given attributes_path.
    Limited to person attributes only.
    TODO can this be combined with the write csv function?
    TODO add household attributes

	:param population: core.Population
	:param plans_path: str path
	:param attributes_path: str path
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
                    'tst': leg.start_time.time(),
                    'tet': leg.end_time.time(),
                    'freq': person.freq,
                }
            )
    pd.DataFrame(record).to_csv(plans_path)

    if attributes_path:
        record = []
        for hid, pid, person in population.people():
            line = person.attributes
            line['hid'] = hid
            line['pid'] = pid
            line['freq']
            record.append(line)
        pd.DataFrame(record).to_csv(attributes_path)


def write_od_matrices(
        population, 
        path : str, 
        leg_filter : Optional[str] = None, 
        person_filter : Optional[str] = None, 
        time_minutes_filter : Optional[List[Tuple[int]]] = None
        ) -> None:

    """
	Write a core population object to tabular O-D weighted matrices.
	Optionally segment matrices by leg attributes(mode/ purpose), person attributes or specific time periods.
    A single filter can be applied each time.
    TODO include freq (assume hh)

	:param population: core.Population
    :param path: directory to write OD matrix files
    :param leg_filter: select between 'Mode', 'Purpose'
    :param person_filter: select between given attribute categories (column names) from person attribute data
    :param time_minutes_filter: a list of tuples to slice times, 
    e.g. [(start_of_slicer_1, end_of_slicer_1), (start_of_slicer_2, end_of_slicer_2), ... ]
	"""
    create_local_dir(path)

    legs = []
    
    for hid, household in population.households.items():
        for pid, person in household.people.items():
            for leg in person.legs:
                data = {
                    'Household ID': hid,
                    'Person ID': pid,
                    'Origin':leg.start_location.area,
                    'Destination': leg.end_location.area,
                    'Purpose': leg.purp,
                    'Mode': leg.mode,
                    'Sequence': leg.seq,
                    'Start time': leg.start_time,
                    'End time': leg.end_time,
                    'Freq': household.freq,
                    }
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
        plans_path : str,
        attributes_path : Optional[str] = None,
        version : int = 11,
        comment : Optional[str] = None,
        household_key : Optional[str] = 'hid'
    ) -> None:
    """
	Write a core population object to matsim xml formats (either version 11 or 12). 
	Note that this requires activity locs to be set (shapely.geomerty.Point).
    TODO add support for PathLib?

	:param population: core.Population, population to be writen to disk
	:param plans_path: str, output path (.xml or .xml.gz)
	:param attributes_path: {str,None}, default None, output_path (.xml and .xml.gz)
	:param version: int {11,12}, matsim version, default 11
	:param comment: {str, None}, default None, optionally add a comment string to the xml outputs
	:param household_key: {str,None}, optionally add household id to person attributes, default 'hid'
	:return: None
	"""
    if version == 12:
        write_matsim_v12(
            population=population,
            path=plans_path,
            comment=comment,
            household_key=household_key
            )
    elif version == 11:
        if attributes_path is None:
            raise UserWarning("Please provide an attributes_path for a (default) v11 write.")
        write_matsim_plans(population, plans_path, comment)
        write_matsim_attributes(population, attributes_path, comment, household_key=household_key)
    else:
        raise UserWarning("Version must be 11 or 12.")


def write_matsim_v12(
    population,
    path : str,
    household_key : Optional[str] = 'hid',
    comment : Optional[str] = None
    ) -> None:
    """
    Write a matsim version 12 output (persons plans and attributes combined).
    TODO write this incrementally: https://lxml.de/api.html#incremental-xml-generation
	:param population: core.Population, population to be writen to disk
	:param path: str, output path (.xml or .xml.gz)
	:param comment: {str, None}, default None, optionally add a comment string to the xml outputs
    :param household_key: {str, None}, default 'hid'
    """

    population_xml = et.Element('population')

    # Add some useful comments
    if comment:
        population_xml.append(et.Comment(comment))
    population_xml.append(et.Comment(f"Created {datetime.today()}"))

    for hid, household in population:
        for pid, person in household:
            if household_key is not None:
                person.attributes[household_key] = hid  # force add hid as an attribute
            person_xml = et.SubElement(population_xml, 'person', {'id': str(pid)})

            attributes_xml = et.SubElement(person_xml, 'attributes', {})
            for k, v in person.attributes.items():
                attribute_xml = et.SubElement(attributes_xml, 'attribute', {'class': 'java.lang.String', 'name': str(k)})
                attribute_xml.text = str(v)

            plan_xml = et.SubElement(person_xml, 'plan', {'selected': 'yes'})
            for component in person[:-1]:
                if isinstance(component, Activity):
                    et.SubElement(plan_xml, 'activity', {
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
            et.SubElement(plan_xml, 'activity', {
                'type': component.act,
                'x': str(float(component.location.loc.x)),
                'y': str(float(component.location.loc.y)),
                }
            )

    write_xml(population_xml, path, matsim_DOCTYPE='population', matsim_filename='population_v6')
    # todo assuming v5?


def write_matsim_plans(
    population,
    path : str,
    comment : Optional[str] = None
    ) -> None:
    """
    Write a matsim version 11 plan output (persons plans only).
    TODO write this incrementally: https://lxml.de/api.html#incremental-xml-generation
	:param population: core.Population, population to be writen to disk
	:param path: str, output path (.xml or .xml.gz)
	:param comment: {str, None}, default None, optionally add a comment string to the xml outputs
    """

    population_xml = et.Element('population')

    # Add some useful comments
    if comment:
        population_xml.append(et.Comment(comment))
    population_xml.append(et.Comment(f"Created {datetime.today()}"))

    for hid, household in population:
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

    write_xml(population_xml, path, matsim_DOCTYPE='population', matsim_filename='population_v5')
    # todo assuming v5?


def write_matsim_attributes(
    population,
    location : str,
    comment : Optional[str] = None,
    household_key : Optional[str] = 'hid'
    ) -> None:
    """
    Write a matsim version 11 attributes output (persons attributes only).
    TODO write this incrementally: https://lxml.de/api.html#incremental-xml-generation
	:param population: core.Population, population to be writen to disk
	:param path: str, output path (.xml or .xml.gz)
	:param comment: {str, None}, default None, optionally add a comment string to the xml outputs
    :param household_key: {str, None}, default 'hid', optionally include the hh ID with given key
    """

    attributes_xml = et.Element('objectAttributes')  # start forming xml

    if comment:
        attributes_xml.append(et.Comment(comment))
    attributes_xml.append(et.Comment(f"Created {datetime.today()}"))

    for hid, household in population:
        for pid, person in household:
            person_xml = et.SubElement(attributes_xml, 'object', {'id': str(pid)})

            attributes = person.attributes
            if household_key:  # add hid to household_key if using household key
                attributes[household_key] = hid
                # TODO write hh attributes or add hh output

            for k, v in attributes.items():
                attribute_xml = et.SubElement(person_xml, 'attribute', {'class': 'java.lang.String', 'name': str(k)})
                attribute_xml.text = str(v)

    write_xml(attributes_xml, location, matsim_DOCTYPE='objectAttributes', matsim_filename='objectattributes_v1')

    # todo assuming v1?


def v11_plans_dtd():
    dtd_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "fixtures", "dtd", "population_v5.dtd"
            )
        )
    return et.DTD(dtd_path)


def object_attributes_dtd():
    dtd_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "fixtures", "dtd", "objectattributes_v1.dtd"
            )
        )
    return et.DTD(dtd_path)


def v12_plans_dtd():
    dtd_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "fixtures", "dtd", "population_v6.dtd"
            )
        )
    return et.DTD(dtd_path)


def dump(
    population,
    dir : str,
    crs : Optional[str] = None,
    to_crs : Optional[str] = "EPSG:4326"
    ) -> None:
    """
    Write a population to disk as tabular data in csv format. Outputs are:
    - households.csv: household ids and attributes
    - people.csv: agent ids and attributes
    - legs.csv: activity plan trip records
    - activities.csv: corresponding plan activities
    If activity locs (shapely.geometry.Point) data is available then geojsons will also be written.
    :param population: core.Population
    :param dir: str, path to output directory
    :param crs: str, population coordinate system (generally we use local grid systems)
    :param to_crs: str, default 'EPSG:4326', output crs, defaults for use in kepler
    """
    to_csv(
        population = population,
        dir = dir,
        crs = crs,
        to_crs = to_crs
    )


def to_csv(
    population,
    dir : str,
    crs : Optional[str] = None,
    to_crs : Optional[str] = "EPSG:4326"
    ) -> None:
    """
    Write a population to disk as tabular data in csv format. Outputs are:
    - households.csv: household ids and attributes
    - people.csv: agent ids and attributes
    - legs.csv: activity plan trip records
    - activities.csv: corresponding plan activities
    If activity locs (shapely.geometry.Point) data is available then geojsons will also be written.
    :param population: core.Population
    :param dir: str, path to output directory
    :param crs: str, population coordinate system (generally we use local grid systems)
    :param to_crs: str, default 'EPSG:4326', output crs, defaults for use in kepler
    """

    create_local_dir(dir)

    hhs = []
    people = []
    acts = []
    legs = []

    for hid, hh in population.households.items():
        hh_data = {
            'hid': hid,
            'freq': hh.freq,
            'zone': hh.location.area,
        }
        if isinstance(hh.attributes, dict):
            hh_data.update(hh.attributes)
        # if hh.location.area is not None:
        #     hh_data['area'] = hh.location.area
        if hh.location.loc is not None:
            hh_data['geometry'] = hh.location.loc

        hhs.append(hh_data)

        for pid, person in hh.people.items():
            people_data = {
                'pid': pid,
                'hid': hid,
                'freq': person.freq,
                'zone': hh.location.area,
            }
            if isinstance(person.attributes, dict):
                people_data.update(person.attributes)
            # if hh.location.area is not None:
            #     people_data['area'] = hh.location.area
            if hh.location.loc is not None:
                people_data['geometry'] = hh.location.loc

            people.append(people_data)

            for seq, component in enumerate(person.plan):
                if isinstance(component, Leg):
                    leg_data = {
                        'pid': pid,
                        'hid': hid,
                        'freq': component.freq,
                        'ozone': component.start_location.area,
                        'dzone': component.end_location.area,
                        'purp': component.purp,
                        'origin activity': person.plan[seq-1].act,
                        'destination activity': person.plan[seq+1].act,
                        'mode': component.mode,
                        'seq': component.seq,
                        'tst': component.start_time,
                        'tet': component.end_time,
                        'duration': str(component.duration),
                    }
                    # if component.start_location.area is not None:
                    #     leg_data['start_area'] = component.start_location.area
                    # if component.end_location.area is not None:
                    #     leg_data['end_area'] = component.end_location.area
                    if component.start_location.loc is not None and component.end_location.loc is not None:
                        leg_data['geometry'] = LineString((component.start_location.loc, component.end_location.loc))

                    legs.append(leg_data)
                
                if isinstance(component, Activity):
                    act_data = {
                        'pid': pid,
                        'hid': hid,
                        'freq': component.freq,
                        'activity': component.act,
                        'seq': component.seq,
                        'start time': component.start_time,
                        'end time': component.end_time,
                        'duration': str(component.duration),
                        'zone': component.location.area,
                    }
                    # if component.location.area is not None:
                    #     act_data['area'] = component.location.area
                    if component.location.loc is not None:
                        act_data['geometry'] = component.location.loc

                    acts.append(act_data)

    hhs = pd.DataFrame(hhs).set_index('hid')
    save_geojson(hhs, crs, to_crs, os.path.join(dir, 'households.geojson'))
    save_csv(hhs, os.path.join(dir, 'households.csv'))

    people = pd.DataFrame(people).set_index('pid')
    save_geojson(people, crs, to_crs, os.path.join(dir, 'people.geojson'))
    save_csv(people, os.path.join(dir, 'people.csv'))

    legs = pd.DataFrame(legs)
    save_geojson(legs, crs, to_crs, os.path.join(dir, 'legs.geojson'))
    save_csv(legs, os.path.join(dir, 'legs.csv'))

    acts = pd.DataFrame(acts)
    save_geojson(acts, crs, to_crs, os.path.join(dir, 'activities.geojson'))
    save_csv(acts, os.path.join(dir, 'activities.csv'))


def save_geojson(df, crs, to_crs, path):
    if 'geometry' in df.columns:
        df = gp.GeoDataFrame(df, geometry='geometry')
        if crs is not None:
            df.crs = crs
            df.to_crs(to_crs, inplace=True)
        df.to_file(path, driver='GeoJSON')


def save_csv(df, path):
    if 'geometry' in df.columns:
        df = df.drop('geometry', axis=1)
    df.to_csv(path)


def write_population_csv(
    list_of_populations : list,
    export_path : str,
    ) -> None:
    """"
    This function creates csv export files of populations, households, people, legs and actvities. 
    This export could be used to share data outside of Python or build an interactive dashboard.
    TODO account for frequency
    
    :param population: core.Population
    :param dir: str, path to output directory
    """
    create_local_dir(export_path)

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
                'Area': hh.location,
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
                'Person ID': pid,
                'Frequency': person.freq
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


def write_benchmarks(
    population,
    dimensions : Optional[List[str]] = None,
    data_fields : Optional[List[str]] = None,
    aggfunc : List[Callable]= [len],
    normalise_by = None,
    colnames = None,
    path = None
):
    """
	Extract user-specified benchmarks from the population.
	:param pam.core.Population population: PAM population
    :param list dimensions: Dimensions to group by. If None, return the disaggregate dataset
    :params list data_fields: The data to summarise. If None, simply count the instances of each group
    :params list of functions aggfunc: A set of functions to apply to each data_field, after grouping by the specified dimensions. For example: [len, sum], [sum, np.mean], [np.sum], etc
    :params list normalise_by: convert calculated values to percentages across the specified -by this field- dimension(s).
    :params list colnames: if different to None, rename the columns of the returned dataset  
    :param str path: directory to write the benchmarks. If None, the functions returns the dataframe instead.

	:return: None if an export path is provided, otherwise Pandas DataFrame 
	"""
    ## collect data
    df = []
    for hid, pid, person in population.people():
        for seq, leg in enumerate(person.legs):
            record = {
                    'pid': pid,
                    'hid': hid,
                    'hzone': person.home,
                    'ozone': leg.start_location.area,
                    'dzone': leg.end_location.area,
                    'seq': seq,
                    'purp': leg.purp,
                    'mode': leg.mode,
                    'tst': leg.start_time.time(),
                    'tet': leg.end_time.time(),
                    'duration': leg.duration / pd.Timedelta(minutes = 1), #duration in minutes                    
                    'euclidean_distance': leg.euclidean_distance,
                    'freq': person.freq,
                }
            record = {**record, **dict(person.attributes)} # add person attributes
            df.append(record)
    df = pd.DataFrame(df)
    
    ## add extra fields used for benchmarking
    df['personhrs'] = df['freq'] * df['duration'] / 60
    df['departure_hour'] = df.tst.apply(lambda x:x.hour)
    df['arrival_hour'] = df.tet.apply(lambda x:x.hour)
    df['euclidean_distance_category'] = pd.cut(
        df.euclidean_distance, 
        bins =[0,1,5,10,25,50,100,200,999999],
        labels = ['0 to 1 km', '1 to 5 km', '5 to 10 km', '10 to 25 km', '25 to 50 km', '50 to 100 km', '100 to 200 km', '200+ km']
    )    
    df['duration_category'] = pd.cut(
        df.duration, 
        bins =[0,5,10,15,30,45,60,90,120,999999],
        labels = ['0 to 5 min', '5 to 10 min', '10 to 15 min', '15 to 30 min', '30 to 45 min', '45 to 60 min', '60 to 90 min', '90 to 120 min', '120+ min']
    )
    
    ## aggregate across specified dimensions
    if dimensions != None:
        if data_fields != None:
            df = df.groupby(dimensions)[data_fields].agg(aggfunc).fillna(0)
        else:
            df = df.value_counts(dimensions)
            
    ## show as percentages
    if normalise_by != None:
        if normalise_by == 'total':
            df = df / df.sum(axis = 0)
        else:
            df = df.groupby(level = normalise_by).transform(lambda x: x / x.sum())     
    df = df.sort_index().reset_index()
    
    ## flatten column MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.map('_'.join).str.strip('_')
    
    ## rename columns
    if colnames != None:
        df.columns = colnames
        
    ## export or return dataframe
    if path != None:
        if path.lower().endswith('.csv'):
            df.to_csv(path, index=False)
        elif path.lower().endswith('.json'):
            df.to_json(path, orient='records')
        else:
            raise ValueError('Please specify a valid csv or json file path.')
    
    return df


#### benchmark wrappers:
def write_distance_benchmark(population, path=None):
    # number of trips by (euclidean) distance category
    return write_benchmarks(population, dimensions = ['euclidean_distance_category'], data_fields= ['freq'], colnames = ['distance', 'trips'], aggfunc = [sum], path=path)

def write_mode_distance_benchmark(population, path=None):
    # number of trips by (euclidean) distance category and mode
    return write_benchmarks(population, dimensions = ['mode','euclidean_distance_category'], data_fields= ['freq'], colnames = ['mode','distance', 'trips'], aggfunc = [sum], path=path)

def write_duration_benchmark(population, path=None):
    # number of trips by duration
    return write_benchmarks(population, dimensions = ['duration_category'], data_fields= ['freq'], colnames = ['duration', 'trips'], aggfunc = [sum], path=path)

def write_mode_duration_benchmark(population, path=None):
    # number of trips by duration and mode
    return write_benchmarks(population, dimensions = ['mode','duration_category'], data_fields= ['freq'], colnames = ['mode','duration', 'trips'], aggfunc = [sum], path=path)

def write_departure_time_benchmark(population, path=None):
    # number of trips by hour of departure
    return write_benchmarks(population, dimensions = ['departure_hour'], data_fields= ['freq'], colnames = ['departure_hour', 'trips'], aggfunc = [sum], path=path)

def write_mode_purpose_split_benchmark(population, path=None):
    # purpose split for each mode
    return write_benchmarks(population, dimensions = ['mode','purp'], data_fields= ['freq'], normalise_by = ['mode'], colnames = ['mode','purpose', 'trips'], aggfunc = [sum])