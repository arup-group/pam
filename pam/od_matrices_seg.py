import pandas as pd

def od_seg(population, path, type_seg=None, mode_seg=None, time_seg=None, purp_seg=None):    
    ozone = []
    dzone = []

    for hid, household in population.households.items():
        for pid, person in household.people.items():
            for p in person.plan:
                if p.act == 'travel':
                    if p.mode == mode_seg:
                        o = p.start_location.area
                        d = p.end_location.area
                        ozone.append(o)
                        dzone.append(d)
                    if person.attributes['occ'] == type_seg:
                        o = p.start_location.area
                        d = p.end_location.area
                        ozone.append(o)
                        dzone.append(d)
                    if p.start_time == time_seg:
                        o = p.start_location.area
                        d = p.end_location.area
                        ozone.append(o)
                        dzone.append(d)
                    if p.purpose == purp_seg:
                        o = p.start_location.area
                        d = p.end_location.area
                        ozone.append(o)
                        dzone.append(d)

    data_dict = {
        'ozone': ozone,
        'dzone': dzone
    }

    df = pd.DataFrame(data=data_dict).set_index('ozone')
    matrix = df.pivot_table(values='dzone', index='ozone', columns='dzone', fill_value=0, aggfunc=len)

    matrix.to_csv(path)


    