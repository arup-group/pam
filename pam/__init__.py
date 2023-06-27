class PAMValidationError(Exception):
    """Custom exception raised for an Activity Plan validation Error."""

    pass


class PAMSequenceValidationError(PAMValidationError):
    """Custom exception raised for an Activity Plan sequence validation Error."""

    pass


class PAMTimesValidationError(PAMValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""

    pass


class PAMInvalidStartTimeError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""

    pass


class PAMInvalidTimeSequenceError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""

    pass


class PAMInvalidEndTimeError(PAMTimesValidationError):
    """Custom exception raised for an Activity Plan Time validation Error."""

    pass


class PAMValidationLocationsError(PAMValidationError):
    """Custom exception raised for an Activity Plan Locations validation Error."""

    pass


class PAMVehicleIdError(PAMValidationError):
    """Custom exception raised for Vehicle not matching Person ID."""

    pass


class InvalidMATSimError(PAMValidationError):
    """Custom exception raised for invalid MATSim."""

    pass
