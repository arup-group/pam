from datetime import datetime


# End Of Day
# END_OF_DAY = datetime(year=1900, month=1, day=1, hour=23, minute=59, second=59)
END_OF_DAY = datetime(year=1900, month=1, day=2, hour=0, minute=0, second=0)


###### FACILITY SAMPLING VARIABLES #########################################################
EXPECTED_EUCLIDEAN_SPEEDS = {
    'average':10,
    'car':20,
    'bus':10, 
    'walk':5, 
    'cycle':15
} # mode speeds expressed as *euclidean* kilometers per hour 

TRANSIT_MODES = ['bus','rail','pt'] # modes for which the maximum walk distance applies
SMALL_VALUE = 0.000001

LONG_TERM_ACTIVITIES = ['work','school','education']
