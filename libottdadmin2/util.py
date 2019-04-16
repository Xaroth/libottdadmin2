#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

import logging
import sys
import types
import operator

from datetime import datetime, timedelta

GAMEDATE_BASE_DATE = datetime(1, 1, 1)
GAMEDATE_BASE_OFFSET = 366


def gamedate_to_datetime(date):
    if date < GAMEDATE_BASE_OFFSET:  # We really only get 0 occasionally, but cover all the cases.
        return datetime.min
    return GAMEDATE_BASE_DATE + timedelta(days=date - GAMEDATE_BASE_OFFSET)


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
            log = logging.getLogger('%s.%s' % (self.__class__.__module__, self.__class__.__name__))
            setattr(self, '_logger', log)
        return log

    def reset_log(self):
        """
        Resets the current created logger.
        """
        if hasattr(self, '_logger'):
            delattr(self, '_logger')


# From Python six ( https://github.com/benjaminp/six / https://six.readthedocs.io/ )

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

if PY3:
    string_types = str,  # noqa
    integer_types = int,  # noqa
    class_types = type,  # noqa
    text_type = str  # noqa
    binary_type = bytes  # noqa

    _meth_self = "__self__"

    def iterkeys(d, **kw):
        return iter(d.keys(**kw))

    def itervalues(d, **kw):
        return iter(d.values(**kw))

    def iteritems(d, **kw):
        return iter(d.items(**kw))

else:
    string_types = basestring,  # noqa
    integer_types = (int, long)  # noqa
    class_types = (type, types.ClassType)
    text_type = unicode  # noqa
    binary_type = str  # noqa

    _meth_self = "im_self"

    def iterkeys(d, **kw):
        return d.iterkeys(**kw)

    def itervalues(d, **kw):
        return d.itervalues(**kw)

    def iteritems(d, **kw):
        return d.iteritems(**kw)

get_method_self = operator.attrgetter(_meth_self)


def ensure_binary(s, encoding='utf-8', errors='strict'):
    """Coerce **s** to `binary_type`.
    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`
    For Python 3:
      - `str` -> encoded to `bytes`
      - `bytes` -> `bytes`
    """
    if isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif isinstance(s, binary_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


def ensure_str(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to `str`.
    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`
    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    if not isinstance(s, (text_type, binary_type)):
        raise TypeError("not expecting type '%s'" % type(s))
    if PY2 and isinstance(s, text_type):
        s = s.encode(encoding, errors)
    elif PY3 and isinstance(s, binary_type):
        s = s.decode(encoding, errors)
    return s


def ensure_text(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to `text_type`.
    For Python 2:
      - `unicode` -> `unicode`
      - `str` -> `unicode`
    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, text_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


__all__ = [
    "LoggableObject",
    "gamedate_to_datetime",
    "datetime_to_gamedate",
    "string_types",
    "integer_types",

    "ensure_binary",
    "ensure_str",
    "ensure_text",
    "get_method_self",
]
