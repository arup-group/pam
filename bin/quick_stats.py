import argparse
import logging
import pandas as pd
from tabulate import tabulate

from pam import read

logging.basicConfig(level=logging.ERROR)

parser = argparse.ArgumentParser()
parser.add_argument("plans_path", help="path to plans.xml")
args = parser.parse_args()

print(f"Loading population plans from {args.plans_path}...")
population = read.read_matsim(args.plans_path, crop=False)

print("Building pre-crop stats...")
stats = population.stats

print("Cropping activity plan components that end after 24 hours...")
for hid, pid, person in population.people():
    person.plan.crop()
    person.plan.autocomplete_matsim()

print("Building post-crop stats...")
clean_stats = population.stats

data = pd.DataFrame({'original plans': stats, 'plans <24 hours': clean_stats})
data['% of original'] = 100 * data['plans <24 hours'] / data['original plans']
data.style.format({
    '% of original': '{:.2f}'.format,
})
print(tabulate(data, headers='keys', tablefmt='psql'))
