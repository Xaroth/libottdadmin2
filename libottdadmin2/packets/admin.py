#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from .registry import send
from .base import SendingPacket, Struct, ValidationError

from ..constants import NETWORK_GAMESCRIPT_JSON_LENGTH, \
                        NETWORK_RCONCOMMAND_LENGTH, \
                        NETWORK_CHAT_LENGTH, NETWORK_PASSWORD_LENGTH, \
                        NETWORK_CLIENT_NAME_LENGTH, NETWORK_REVISION_LENGTH
from ..util import datetime_to_gamedate

from ..enums import UpdateType, UpdateFrequency, Action, DestType

try:
    import json
except ImportError:
    import simplejson as json 

@send.packet
class AdminJoin(SendingPacket):
    packetID = 0

    def encode(self, password, name, version):
        if not isinstance(password, basestring):
            raise ValidationError("Password is not a string")
        if not isinstance(name, basestring):
            raise ValidationError("Name is not a string")
        if not isinstance(version, basestring):
            raise ValidationError("Version is not a string")
        if len(password) >= NETWORK_PASSWORD_LENGTH:
            raise ValidationError("Password can not exceed %d characters in length (%d)" % (NETWORK_PASSWORD_LENGTH, len(password)))
        yield self.pack_str(password)
        yield self.pack_str(name[:NETWORK_CLIENT_NAME_LENGTH])
        yield self.pack_str(version[:NETWORK_REVISION_LENGTH])

@send.packet
class AdminQuit(SendingPacket):
    packetID = 1

@send.packet
class AdminUpdateFrequency(SendingPacket):
    packetID = 2
    format = Struct.create("HH")

    def encode(self, updateType, updateFreq):
        if not UpdateType.is_valid(updateType):
            raise ValidationError("Invalid updateType: '%r'" % updateType)
        if not UpdateFrequency.is_valid(updateFreq):
            raise ValidationError("Invalid updateFreq: '%r'" % updateFreq)
        yield self.pack(self.format, updateType, updateFreq)

@send.packet
class AdminPoll(SendingPacket):
    packetID = 3
    format = Struct.create("BI")

    def encode(self, pollType, extra):
        if not UpdateType.is_valid(pollType):
            raise ValidationError("Invalid pollType: '%r'" % pollType)
        yield self.pack(self.format, pollType, extra)

@send.packet
class AdminChat(SendingPacket):
    packetID = 4
    format = Struct.create("BBI")

    def encode(self, action, destType, clientID, message):
        if not isinstance(action, (int, long)):
            raise ValidationError("action is not an int")
        if action not in [
            Action.CHAT,
            Action.CHAT_CLIENT,
            Action.CHAT_COMPANY,
            Action.SERVER_MESSAGE,
            ]:
            raise ValidationError("Unable to send a message of type: %r" % action)
        if not DestType.is_valid(destType):
            raise ValidationError("Invalid destType: %r" % destType)
        if not isinstance(message, basestring):
            raise ValidationError("Message is not a string")
        if len(message) > NETWORK_CHAT_LENGTH:
            raise ValidationError("Message can not exceed %d characters in length (%d)" % (NETWORK_CHAT_LENGTH, len(message)))
        yield self.pack(self.format, action, destType, clientID)
        yield self.pack_str(message)

@send.packet
class AdminRcon(SendingPacket):
    packetID = 5

    def encode(self, command):
        if not isinstance(command, basestring):
            raise ValidationError("Command is not a string")
        if len(command) >= NETWORK_RCONCOMMAND_LENGTH:
            raise ValidationError("Rcon commands can not exceed %d characters in length (%d)" % (NETWORK_RCONCOMMAND_LENGTH, len(command)))
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

@send.packet
class AdminPing(SendingPacket):
    packetID = 7
    format = Struct.create("I")

    def encode(self, payload):
        yield self.pack(self.format, payload)
