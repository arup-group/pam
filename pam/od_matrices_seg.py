import os
import pandas as pd
from datetime import datetime
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY

def od_filtered(population, path, leg_filter = None, person_filter = None):   
    """
    Function to create an od matrix filtered on leg attributes (mode/purpose) or person attributes.
    :param path: directory to locate the written files
    :param population: core.Population
    :param leg_filter: select between 'Mode', 'Purpose'
    :param person_filter: select between given attribute categories from person attribute data
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
                            'Purpose': leg.purpose,
                            'Mode': leg.mode,
                             'Sequence': leg.seq,
                            'Start time': leg.start_time,
                            'End time': leg.end_time}
                
                if person_filter:
                    legs.append({**data, **person.attributes})
                else:
                    legs.append(data)         
                                
    data_legs = pd.DataFrame(data=legs)
    
    if leg_filter:
        data_legs_grouped=data_legs.groupby(leg_filter)   
        
    if person_filter:
        data_legs_grouped=data_legs.groupby(person_filter)            

    for filter, leg in data_legs_grouped:
        df = pd.DataFrame(data=leg, columns = ['Origin','Destination']).set_index('Origin')
        matrix = df.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
        matrix.to_csv(os.path.join(path, filter+'_od.csv'))