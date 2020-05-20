import pandas as pd
from datetime import datetime
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY

def od_filtered(population, path, leg_filter = None):   
    """
    Function to create an od matrix filtered on mode, type, time or purpose.
    Note that time is in minutes.
    :param path: directory to locate the written files
    :param population: core.Population
    :param leg_filter: select between 'Mode', 'Purpose'
    :return: None
    """

    legs = []

    for hid, household in population.households.items():
        for pid, person in household.people.items():
            for leg in person.legs:
                legs.append({'Household ID': hid,
                            'Person ID': pid,
                            'Origin':leg.start_location.area,
                            'Destination': leg.end_location.area,
                            'Purpose': leg.purpose,
                            'Mode': leg.mode,
                            'Sequence': leg.seq,
                            'Start time': leg.start_time,
                            'End time': leg.end_time,
                            'Duration': str(leg.duration)})
                
    data_legs = pd.DataFrame(data=legs)
    
    if leg_filter:
        data_legs_grouped=data_legs.groupby(leg_filter)            

        for filter, leg in data_legs_grouped:
            df = pd.DataFrame(data=leg, columns = ['Origin','Destination']).set_index('Origin')
            matrix = df.pivot_table(values='Destination', index='Origin', columns='Destination', fill_value=0, aggfunc=len)
            matrix.to_csv(os.path.join(path, filter+'_od.csv'))