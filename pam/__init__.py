class PAMValidationError(Exception):
    """
    Custom exception raised for an Activity Plan validation Error.
    """

    pass


class PAMSequenceValidationError(PAMValidationError):
    """
    Custom exception raised for an Activity Plan sequence validation Error.
    """

    pass


class PAMTimesValidationError(PAMValidationError):
    """
    Custom exception raised for an Activity Plan Time validation Error.
    """

    pass


class PAMValidationLocationsError(PAMValidationError):
    """
    Custom exception raised for an Activity Plan Locations validation Error.
    """

    pass
