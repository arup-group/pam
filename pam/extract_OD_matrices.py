import os
import pandas as pd
from pam.activity import Plan, Activity, Leg
from pam.core import Population, Household, Person

# 1.if activity is travel, I'd like to add origin and destination locations into a list respectively
# 2.create a dataframe which has the first column as ozone and the second column dzone
# 3.pivot table
# 4.Write csv (df.to_csv('OD_matrices.csv'))


def extract_od(population):
    ozone = []
    dzone = []

    for hid, household in population.households.items():
        for pid, person in household.people.items():
            for p in person.plan:
                if p.act == 'travel':
                    o = p.start_location
                    d = p.end_location
                    ozone.append(o)
                    dzone.append(d)

    dataDict = {
        'ozone': ozone,
        'dzone': dzone
    }

    df = pd.DataFrame(data = dataDict).set_index('ozone')

    print(df)

    df.pivot_table(values='dzone', index='ozone', columns='dzone', fill_value=0, aggfunc=len)
        
    ## https://stackoverflow.com/questions/60079115/create-origin-destination-matrix-from-a-data-frame-in-python
    ## https://stackoverflow.com/questions/56520616/is-it-possible-from-dataframe-transform-to-matrix
    ## https://stackoverflow.com/questions/43298192/valueerror-grouper-for-something-not-1-dimensional/52090527
    


extract_od(population)