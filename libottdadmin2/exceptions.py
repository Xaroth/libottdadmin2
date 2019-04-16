#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#


class OttdException(Exception):
    pass


class InvalidHeaderError(OttdException):
    pass


class UnknownPacketError(OttdException):
    pass


class InvalidPacketLengthError(OttdException):
    pass


class PacketExhaustedError(OttdException):
    pass
