from libottdadmin2.util import LoggableObject

class InvalidPacketItem(Exception):
    pass

class PacketNotFound(Exception):
    pass

class PacketRegistry(LoggableObject):
    def __init__(self):
        self._packets = {}

    def packet(self, packetID, klass = None):
        if packetID is None and klass is None:
            # @register.packet()
            return self.packet_func
        elif packetID is not None and klass is None:
            if callable(packetID):
                # @register.packet
                return self.packet_func(packetID)
            else:
                # @register.packet(packetID) / @register.packet(packetID=packetID)
                def dec(func):
                    return self.item(packetID, func)
                return dec
        elif packetID is not None and klass is not None:
            # register.packet(packetID, klass)
            self.log.debug("Registering packetID '%d' to class '%s.%s'", 
                            packetID, klass.__module__, klass.__name__)
            self._packets[packetID] = klass()
            return klass
        else:
            raise InvalidPacketItem("Unsupported argument to .packet(packetID, klass)")

    def __iter__(self):
        return self._packets.itervalues()

    def __getitem__(self, id):
        if not isinstance(id, (int, long)):
            if hasattr(id, 'packetID'):
                id = id.packetID
        packet = self._packets.get(id, None)
        if packet is None:
            raise PacketNotFound("Packet with id '%d' not found" % id)
        return packet

    def packet_func(self, klass):
        packetID = getattr(klass, 'packetID', None)
        if packetID is None:
            raise InvalidPacketItem("Packet class '%s.%s' has no packetID" %
                            (klass.__module__, klass.__name__))
        self.packet(packetID, klass)
        return klass

receive     = PacketRegistry()
send        = PacketRegistry() # Not really super useful to register a pool of sending packets, but at least we have a easy-to-access list this way.