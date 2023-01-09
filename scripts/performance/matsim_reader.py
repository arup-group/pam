import argparse

from pam import read

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Build a PAM population from matsim plans')
    arg_parser.add_argument('-p',
                            '--plans',
                            help='the path to the matsim plans file',
                            required=True)
    args = vars(arg_parser.parse_args())
    plans = args['plans']
    print(f"Building PAM population from MATSim plans {plans}")

    population = read.read_matsim(plans_path=plans)

    print("Created population '{}'".format(population))
