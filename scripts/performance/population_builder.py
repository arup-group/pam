import argparse

import pandas as pd

from pam import read

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Build a PAM population from travel diaries and person attributes')
    arg_parser.add_argument('-t',
                            '--travel-diary',
                            help='the path to the CSV travel diaries file',
                            required=True)
    arg_parser.add_argument('-a',
                            '--person-attributes',
                            help='the path to the CSV person attributes file',
                            required=True)
    args = vars(arg_parser.parse_args())
    travel_diary = args['travel_diary']
    person_attributes = args['person_attributes']
    print("Building PAM population from travel diaries {} and person attributes {}"
          .format(travel_diary, person_attributes))

trips = pd.read_csv(travel_diary)
attributes = pd.read_csv(person_attributes)
attributes.set_index('pid', inplace=True)
population = read.load_travel_diary(trips, attributes)

print("Created population '{}'".format(population))
