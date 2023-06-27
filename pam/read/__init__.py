import pickle

from pam.read.diary import *
from pam.read.matsim import *


def load_pickle(path):
    with open(path, "rb") as file:
        return pickle.load(file)
