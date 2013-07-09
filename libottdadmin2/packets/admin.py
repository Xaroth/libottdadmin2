from libottdadmin2.packets.registry import send
from libottdadmin2.packets.base import SendingPacket, Struct
from libottdadmin2.util import datetime_to_gamedate

@send.packet
class AdminJoin(SendingPacket):
    packetID = 0

    def encode(self, password, name, version):
        yield self.pack_str(password)
        yield self.pack_str(name)
        yield self.pack_str(version)

@send.packet
class AdminQuit(SendingPacket):
    packetID = 1

@send.packet
class AdminUpdateFrequency(SendingPacket):
    packetID = 2
    format = Struct.create("HH")

    def encode(self, updateType, updateFreq):
        yield self.pack(self.format, updateType, updateFreq)

@send.packet
class AdminPoll(SendingPacket):
    packetID = 3
    format = Struct.create("BI")

    def encode(self, pollType, extra):
        yield self.pack(self.format, pollType, extra)

@send.packet
class AdminChat(SendingPacket):
    packetID = 4
    format = Struct.create("BBI")

    def encode(self, action, destType, clientID, message):
        yield self.pack(self.format, action, destType, clientID)
        yield self.pack_str(message)

@send.packet
class AdminRcon(SendingPacket):
    packetID = 5

    def encode(self, command):
        yield self.pack_str(command)

@send.packet
class AdminGamescript(SendingPacket):
    packetID = 6

    def encode(self):
        pass
