#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from struct import Struct as OrigStruct

from libottdadmin2.util import LoggableObject, ensure_binary, ensure_text, integer_types

STRUCT_FORMAT_PREFIXES = {'@', '=', '<', '>', '!'}


class Struct(OrigStruct):
    """
    We overload the original struct.Struct class
    so we can force the proper endianness.
    """

    _structCache = {}

    @classmethod
    def create(cls, fmt):
        """
        Creates a Struct object with the specified format.

        However, the created Struct objects are cached, so that
        only one Struct object exists for a specific format.
        """
        item = cls._structCache.get(fmt, None)
        if item is None:
            item = cls._structCache[fmt] = Struct(fmt)
        return item

    def __init__(self, fmt):
        if fmt[0] in STRUCT_FORMAT_PREFIXES:
            fmt = fmt[1:]
        fmt = '<%s' % fmt
        super(Struct, self).__init__(fmt)


def pack(fmt, *args):
    return fmt.pack(*args)


def unpack(fmt, data, index=0):
    values = fmt.unpack_from(data, index)
    if len(values) == 1:
        return values[0]
    return values


def pack_str(string):
    return b'%s\x00' % ensure_binary(string)


def unpack_str(data, index=0):
    try:
        found_pos = data.index(b'\x00', index)
        return ensure_text(data[index:found_pos])
    except ValueError:
        raise


class ValidationError(Exception):
    """
    Raised when a packet fails to encode to its stream value.
    """
    pass


class Packet(LoggableObject):
    packetID = None

    @classmethod
    def pack(self, format, *args):
        return pack(format, *args)

    @classmethod
    def unpack(self, format, data, index=0):
        return unpack(format, data, index)

    @classmethod
    def pack_str(self, string):
        return pack_str(string)

    @classmethod
    def unpack_str(self, data, index=0):
        return unpack_str(data, index)

    def __eq__(self, other):
        if isinstance(other, integer_types):
            return self.packetID == other
        try:
            return self.packetID == other.packetID
        except (AttributeError, TypeError, ValueError):
            pass
        return False

    def __unicode__(self):
        return self.__class__.__name__
    __str__ = __unicode__

    def __repr__(self):
        return "<PacketID: %d :: %s>" % (self.packetID or -1, self.__class__.__name__)


class SendingPacket(Packet):
    format_packetid = Struct.create("B")
    format_packetlen = Struct.create("H")

    def __call__(self, **kwargs):
        data = [
            None,
            self.pack(self.format_packetid, self.packetID)
        ]
        length = self.format_packetid.size + self.format_packetlen.size
        for part in (self.encode(**kwargs) or []):
            if isinstance(part, (list, tuple)):
                length += part[1]
                part = part[0]
            else:
                length += len(part)
            data.append(part)
        data[0] = self.pack(self.format_packetlen, length)
        return b''.join(data)

    def encode(self, **kwargs):
        return


class ReceivingPacket(Packet):
    def __call__(self, data):
        return self.decode(data)

    def decode(self, data):
        return
