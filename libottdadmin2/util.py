#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

import logging

from datetime import datetime, timedelta

GAMEDATE_BASE_DATE = datetime(1, 1, 1)
GAMEDATE_BASE_OFFSET = 366

def gamedate_to_datetime(date):
    if date < GAMEDATE_BASE_OFFSET: # We really only get 0 occasionally, but cover all the cases.
        return datetime.min
    return GAMEDATE_BASE_DATE + timedelta(days = date  - GAMEDATE_BASE_OFFSET)

def datetime_to_gamedate(datetime):
    return (datetime - GAMEDATE_BASE_DATE).days + GAMEDATE_BASE_OFFSET

class LoggableObject(object):
    """
    Loggable Object MixIn.

    This exposes the .log property, which dynamically creates a logging.logger formatted for the class.
    """

    @property
    def log(self):
        """
        The log property. retrieving this the first time will generate a logging.logger for the inheriting class.
        """
        log = getattr(self, '_logger', None)
        if log is None:
            log = logging.getLogger('%s.%s' % (
                                                self.__class__.__module__, 
                                                self.__class__.__name__))
            setattr(self, '_logger', log)
        return log

    def reset_log(self):
        """
        Resets the current created logger.
        """
        if hasattr(self, '_logger'):
            delattr(self, '_logger')
