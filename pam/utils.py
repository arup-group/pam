from datetime import datetime


def minutes_to_datetime(minutes: int):
    """
    Convert minutes to datetime
    :param minutes: int
    :return: datetime
    """
    assert minutes < 24 * 60
    hours = minutes // 60
    minutes = minutes % 60
    return datetime(2020, 4, 2, hours, minutes)
