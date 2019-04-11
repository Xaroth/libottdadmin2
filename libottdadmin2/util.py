#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

import logging
import re

from datetime import datetime, timedelta

GAMEDATE_BASE_DATE = datetime(1, 1, 1)
GAMEDATE_BASE_OFFSET = 366


def gamedate_to_datetime(date):
    if date < GAMEDATE_BASE_OFFSET:  # We really only get 0 occasionally, but cover all the cases.
        return datetime.min
    return GAMEDATE_BASE_DATE + timedelta(days=date - GAMEDATE_BASE_OFFSET)


def datetime_to_gamedate(dt):
    if dt == datetime.min:
        return 0
    return (dt - GAMEDATE_BASE_DATE).days + GAMEDATE_BASE_OFFSET


def loggable(klass: type):
    klass.log = logging.getLogger("%s.%s" % (klass.__module__, klass.__name__))
    return klass


class SimpleDataclass:
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)

    def __repr__(self):
        return "<%s(**%r)>" % (self.__class__.__name__, self.__dict__)


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def ensure_binary(s, encoding='utf-8', errors='strict'):
    if isinstance(s, str):
        return s.encode(encoding, errors)
    elif isinstance(s, bytes):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


def ensure_text(s, encoding='utf-8', errors='strict'):
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    elif isinstance(s, str):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


__all__ = [
    "loggable",
    "SimpleDataclass",
    "gamedate_to_datetime",
    "datetime_to_gamedate",
    "camel_to_snake",
    "ensure_binary",
    "ensure_text",
]
