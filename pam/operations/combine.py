from datetime import datetime
import shutil
from pam import read, write, core
import os

def pop_combine(inpaths, matsim_version):

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
            version=matsim_version
            )
        print(f"population: {population.stats}") 
        
        combined_population += population

    return combined_population
