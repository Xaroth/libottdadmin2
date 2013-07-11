#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from .registry import send
from .base import SendingPacket, Struct, ValidationError

from ..constants import NETWORK_GAMESCRIPT_JSON_LENGTH
from ..util import datetime_to_gamedate

try:
    import json
except ImportError:
    import simplejson as json 

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

    def encode(self, data = None, json_string = None):
        if json_string is None and data is not None:
            json_string = json.dumps(data)
        if json_string is None:
            raise ValidationError("Please specify either the data object to serialize, or the json string directly.")
        if len(json_string) >= NETWORK_GAMESCRIPT_JSON_LENGTH:
            raise ValidationError("Data object serializes to a json string that's too long to send.")
        yield self.pack_str(json_string)
        
class AdminPing(SendingPacket):
    packetID = 7
    format = Struct.create("I")

    def encode(self, payload):
        if not isinstance(payload, (int, long)):
            raise ValidationError("Please specify a uint32 value as payload")
        if payload > 0xFFFF:
            raise ValidationError("Please specify a uint32 value as payload (%d > %d)" % (payload, 0xFFFF))
        yield self.pack(self.format, payload)