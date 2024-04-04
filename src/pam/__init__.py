"""Top-level module for pam."""

import pyproj

__author__ = """Fred Shone"""  # triple quotes in case the name has quotes in it.
__email__ = "fred.shone@arup.com"
__version__ = "0.3.2"


pyproj.network.set_network_enabled(False)


class PAMValidationError(Exception):
    """Custom exception raised for an Activity Plan validation Error."""


class PAMSequenceValidationError(PAMValidationError):
    """Custom exception raised for an Activity Plan sequence validation Error."""


class PAMTimesValidationError(PAMValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""


class PAMInvalidStartTimeError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""


class PAMInvalidTimeSequenceError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""


class PAMInvalidEndTimeError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""


class PAMValidationLocationsError(PAMValidationError):
    """Custom exception raised for an Activity Plan Locations validation Error."""


class PAMVehicleIdError(PAMValidationError):
    """Custom exception raised for Vehicle not matching Person ID."""


class PAMVehicleTypeError(PAMValidationError):
    """Custom exception raised for Vehicle type error."""


class InvalidMATSimError(PAMValidationError):
    """Custom exception raised for invalid MATSim."""
