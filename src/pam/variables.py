from datetime import datetime

# default datetimes for plan start and end (24 hours)
START_OF_DAY = datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0)
END_OF_DAY = datetime(year=1900, month=1, day=2, hour=0, minute=0, second=0)


###### FACILITY SAMPLING VARIABLES #########################################################
EXPECTED_EUCLIDEAN_SPEEDS = {
    "average": 10 * 1000 / 3600,
    "car": 20 * 1000 / 3600,
    "bus": 10 * 1000 / 3600,
    "rail": 15 * 1000 / 3600,
    "pt": 15 * 1000 / 3600,
    "subway": 15 * 1000 / 3600,
    "walk": 5 * 1000 / 3600,
    "cycle": 15 * 1000 / 3600,
    "freight": 50 * 1000 / 3600,
}  # mode speeds expressed as *euclidean* meters per second

TRANSIT_MODES = ["bus", "rail", "pt", "subway"]  # modes for which the maximum walk distance applies
SMALL_VALUE = 0.000001

LONG_TERM_ACTIVITIES = ["work", "school", "education", "home"]

DEFAULT_ACTIVITIES_PLOT_WIDTH = 16
DEFAULT_ACTIVITIES_FONTSIZE = 10
