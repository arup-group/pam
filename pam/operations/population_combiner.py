from datetime import datetime
import shutil
from pam import read, write, core
import os
#import poptii_utils

def pop_combine(inpaths):

    """
    Combine two or more populations (e.g. household, freight... etc).

    """
    print("==================================================")
    print(f"Combining input populations")

    combined_population = core.Population()

    for inpath in inpaths:
     
        population = read.read_matsim(
            os.path.join(inpath, "plans.xml"),
            household_key="hid",
            weight=1,
            version=12
            )
        print(f"population: {population.stats}") 
        
        combined_population += population

    return combined_population



# def dump_population(
#     project_name,
#     population,
#     outpath,
#     crs,
#     matsim_version=12):

#     """
#     Export combined population to MatSIM format

#     """

#     if os.path.isdir(outpath)==False:
#         os.mkdir(outpath)

#     write.write_matsim(
#         population,
#         version=matsim_version,
#         plans_path=os.path.join(outpath, 'population.xml'),
#         comment=f'{project_name} {datetime.now()}'
#     )
    
#     population.to_csv(outpath, crs=crs, to_crs="EPSG:27700")
        
