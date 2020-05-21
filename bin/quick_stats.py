import argparse
import logging

from pam import read


parser = argparse.ArgumentParser()
parser.add_argument("plans_path", help="path to plans.xml")
args = parser.parse_args()


print(f"Loading population plans from {args.plans_path}")
print("...")
population = read.read_matsim(args.plans_path)

print("Building stats...")
stats = population.stats

for k, v in stats.items():
    print(f"{k}: {v}")

print("Done")