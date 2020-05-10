import argparse

import pandas as pd

from pam import parse


def scale_people(seed_people_df, scale_factor):
    num_seed_people = len(seed_people_df.index)
    num_people_required = num_seed_people * scale_factor
    print('Creating {} synthetic people from {} people in seed population...'
          .format(num_people_required, num_seed_people))
    return pd.concat([seed_people_df] * scale_factor, ignore_index=True)


def scale_trips(seed_trips_df, scale_factor):
    num_seed_trips = len(seed_trips_df.index)
    num_trips_required = num_seed_trips * scale_factor
    print('Creating {} synthetic trips from {} trips in seed population...'
          .format(num_trips_required, num_seed_trips))
    scaled_df = pd.concat([seed_trips_df] * scale_factor, ignore_index=True)

    # now fix up PIDs and HIDs so that all new trips become unique
    num_seed_people = len(seed_trips_df.pid.unique())
    num_seed_households = len(seed_trips_df.hid.unique())
    for i, row in scaled_df.iterrows():
        if i < num_seed_trips:
            continue
        tranche_number, remainder = divmod(i, num_seed_trips)
        old_pid = scaled_df.at[i, 'pid']
        old_hid = scaled_df.at[i, 'hid']
        new_pid = old_pid + (tranche_number * num_seed_people)
        new_hid = old_hid + (tranche_number * num_seed_households)
        print("Fixing values for row {} in synthesised tranch {} - old pid:{} -> new pid: {}, old hid:{} -> new hid:{}"
              .format(i, tranche_number, old_pid, new_pid, old_hid, new_hid))
        scaled_df.at[i, 'pid'] = new_pid
        scaled_df.at[i, 'hid'] = new_hid
    return scaled_df


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Build synthetic PAM travel diaries and person attributes from seed data')
    arg_parser.add_argument('-t',
                            '--travel-diary',
                            help='the path to the seed CSV travel diaries file',
                            required=True)
    arg_parser.add_argument('-a',
                            '--person-attributes',
                            help='the path to the seed CSV person attributes file',
                            required=True)
    arg_parser.add_argument('-o',
                            '--output-dir',
                            help='the path to the directory where new CSV files will be created',
                            required=True)
    arg_parser.add_argument('-sf',
                            '--scale-factor',
                            help='the factor by which to scale up the numbers of seed users and trips',
                            type=int)
    args = vars(arg_parser.parse_args())
    travel_diary = args['travel_diary']
    person_attributes = args['person_attributes']
    output_dir = args['output_dir']
    scale_factor = args['scale_factor']
    print("Creating synthetic PAM travel diary entries and people in {} by scaling seed files {} & {} up X {}"
          .format(output_dir, travel_diary, person_attributes, scale_factor))

    seed_trips = pd.read_csv(travel_diary)
    seed_people = pd.read_csv(person_attributes)
    seed_people.set_index('pid', inplace=True)
    seed_population = parse.load_travel_diary(seed_trips, seed_people)
    print("Created seed population from input files: '{}'".format(seed_population))

    people_df = scale_people(seed_people, scale_factor)
    trips_df = scale_trips(seed_trips, scale_factor)
    print('Finished creating raw synthetic data')

    print('Building population from raw synthetic data')
    population = parse.load_travel_diary(trips_df, people_df)
    print("Created synthetic population: '{}'".format(population))

    print('Writing synthetic data out to {}'.format(output_dir))
