import json

from libottdadmin2.constants import NETWORK_CLIENT_NAME_LENGTH, NETWORK_REVISION_LENGTH, NETWORK_PASSWORD_LENGTH, \
    NETWORK_CHAT_LENGTH, NETWORK_RCONCOMMAND_LENGTH, NETWORK_GAMESCRIPT_JSON_LENGTH
from libottdadmin2.packets.base import Packet, check_length
from libottdadmin2.enums import UpdateType, UpdateFrequency, ChatAction, DestType


@Packet.register
class AdminJoin(Packet):
    packet_id = 0
    fields = ['password', 'name', 'version']

    def encode(self, password, name, version):
        self.write_str(check_length(password, NETWORK_PASSWORD_LENGTH, "'password'"),
                       check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"),
                       check_length(version, NETWORK_REVISION_LENGTH, "'version'"))

    def decode(self):
        password, name, version = self.read_str(3)
        return self.data(check_length(password, NETWORK_PASSWORD_LENGTH, "'password'"),
                               check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"),
                               check_length(version, NETWORK_REVISION_LENGTH, "'version'"))


@Packet.register
class AdminQuit(Packet):
    packet_id = 1


@Packet.register
class AdminUpdateFrequency(Packet):
    packet_id = 2
    fields = ['type', 'freq']

    def encode(self, type: UpdateType, freq: UpdateFrequency):
        self.write_ushort(UpdateType(type), UpdateFrequency(freq))

    def decode(self):
        type, freq = self.read_ushort(2)
        return self.data(UpdateType(type), UpdateFrequency(freq))


@Packet.register
class AdminPoll(Packet):
    packet_id = 3
    fields = ['type', 'extra']

    def encode(self, type, extra):
        self.write_byte(UpdateType(type))
        self.write_uint(extra)

    def decode(self):
        _type, extra = self.read_data(['byte', 'uint'])
        return self.data(UpdateType(_type), extra)


@Packet.register
class AdminChat(Packet):
    packet_id = 4
    fields = ['action', 'type', 'client_id', 'message']

    def encode(self, action: ChatAction, type: DestType, client_id, message):
        self.write_byte(ChatAction(action))
        self.write_byte(DestType(type))
        self.write_uint(client_id)
        self.write_str(check_length(message, NETWORK_CHAT_LENGTH, "'message'"))

    def decode(self):
        action, _type, client_id = self.read_data(['byte', 'byte', 'uint'])
        message, = self.read_str()
        # TODO: convert to enum
        return self.data(ChatAction(action), DestType(_type), client_id,
                               check_length(message, NETWORK_CHAT_LENGTH, "'message'"))


@Packet.register
class AdminRcon(Packet):
    packet_id = 5
    fields = ['command']

    def encode(self, command):
        self.write_str(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))

    def decode(self):
        command, = self.read_str()
        return self.data(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))


@Packet.register
class AdminGamescript(Packet):
    packet_id = 6
    fields = ['json_data']

    def encode(self, json_data):
        json_string = json.dumps(json_data)
        self.write_str(check_length(json_string, NETWORK_GAMESCRIPT_JSON_LENGTH, "'json_data'"))

    def decode(self):
        json_string, = self.read_str()
        json_data = json.loads(check_length(json_string, NETWORK_GAMESCRIPT_JSON_LENGTH, "'json_data'"))
        return self.data(json_data)


@Packet.register
class AdminPing(Packet):
    packet_id = 7
    fields = ['payload']

    def encode(self, payload):
        self.write_uint(payload)

    def decode(self):
        payload, = self.read_uint()
        return self.data(payload)

