from struct import Struct as OrigStruct

class Struct(OrigStruct):
    """
    We overload the original struct.Struct class
    so we can force the proper endianness.
    """

    _structCache = {}

    @classmethod
    def create(cls, format):
        """
        Creates a Struct object with the specified format.

        However, the created Struct objects are cached, so that
        only one Struct object exists for a specific format.
        """
        item = cls._structCache.get(format, None)
        if item is None:
            item = cls._structCache[format] = Struct(format)
        return item

    def __init__(self, format):
        if format[0] in ['@', '=', '<', '>', '!',]:
            format = format[1:]
        format = '<%s' % format
        super(Struct, self).__init__(format)

def pack(format, *args):
    return format.pack(*args)

def unpack(format, data, index = 0):
    values = format.unpack_from(data, index)
    if len(values) == 1:
        return values[0]
    return values

def pack_str(string):
    return '%s\x00' % string

def unpack_str(data, index = 0):
    try:
        found_pos = data.index('\x00', index)
        return data[index:found_pos]
    except ValueError:
        raise

class Packet(object):
    packetID = None
    @classmethod
    def pack(self, format, *args):
        return pack(format, *args)

    @classmethod
    def unpack(self, format, data, index = 0):
        return unpack(format, data, index)

    @classmethod
    def pack_str(self, string):
        return pack_str(string)

    @classmethod
    def unpack_str(self, data, index = 0):
        return unpack_str(data, index)


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
        return ''.join(data)

    def encode(self, **kwargs):
        return

class ReceivingPacket(Packet):
    def __call__(self, data):
        return self.decode(data)

    def decode(self, data):
        return
