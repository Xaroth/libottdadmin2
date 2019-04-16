#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

import json
from typing import Tuple, Union

from libottdadmin2.constants import NETWORK_CLIENT_NAME_LENGTH, NETWORK_REVISION_LENGTH, NETWORK_PASSWORD_LENGTH, \
    NETWORK_CHAT_LENGTH, NETWORK_RCONCOMMAND_LENGTH, NETWORK_GAMESCRIPT_JSON_LENGTH
from libottdadmin2.packets.base import Packet, check_length
from libottdadmin2.enums import UpdateType, UpdateFrequency, ChatAction, DestType, PollExtra


@Packet.register
class AdminJoin(Packet):
    packet_id = 0
    fields = ['password', 'name', 'version']

    def encode(self, password: str, name: str, version: str):
        self.write_str(check_length(password, NETWORK_PASSWORD_LENGTH, "'password'"),
                       check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"),
                       check_length(version, NETWORK_REVISION_LENGTH, "'version'"))

    def decode(self) -> Tuple[str, str, str]:
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

    # noinspection PyShadowingBuiltins
    def encode(self, type: UpdateType, freq: UpdateFrequency):
        self.write_ushort(UpdateType(type), UpdateFrequency(freq))

    def decode(self):
        _type, freq = self.read_ushort(2)
        return self.data(UpdateType(_type), UpdateFrequency(freq))


@Packet.register
class AdminPoll(Packet):
    packet_id = 3
    fields = ['type', 'extra']

    # noinspection PyShadowingBuiltins
    def encode(self, type: UpdateType, extra: Union[int, PollExtra]):
        self.write_byte(UpdateType(type))
        self.write_uint(extra)

    def decode(self) -> Tuple[UpdateType, Union[int, PollExtra]]:
        _type, extra = self.read_data(['byte', 'uint'])
        return self.data(UpdateType(_type), extra)


@Packet.register
class AdminChat(Packet):
    packet_id = 4
    fields = ['action', 'type', 'client_id', 'message']

    # noinspection PyShadowingBuiltins
    def encode(self, action: ChatAction, type: DestType, client_id: int, message: str):
        self.write_byte(ChatAction(action))
        self.write_byte(DestType(type))
        self.write_uint(client_id)
        self.write_str(check_length(message, NETWORK_CHAT_LENGTH, "'message'"))

    def decode(self) -> Tuple[ChatAction, DestType, int, str]:
        action, _type, client_id = self.read_data(['byte', 'byte', 'uint'])
        message, = self.read_str()
        return self.data(ChatAction(action), DestType(_type), client_id,
                         check_length(message, NETWORK_CHAT_LENGTH, "'message'"))


@Packet.register
class AdminRcon(Packet):
    packet_id = 5
    fields = ['command']

    def encode(self, command: str):
        self.write_str(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))

    def decode(self) -> Tuple[str]:
        command, = self.read_str()
        return self.data(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))


@Packet.register
class AdminGamescript(Packet):
    packet_id = 6
    fields = ['json_data']

    def encode(self, json_data: Union[dict, list, str]):
        json_string = json.dumps(json_data)
        self.write_str(check_length(json_string, NETWORK_GAMESCRIPT_JSON_LENGTH, "'json_data'"))

    def decode(self) -> Tuple[Union[list, dict, str]]:
        json_string, = self.read_str()
        json_data = json.loads(check_length(json_string, NETWORK_GAMESCRIPT_JSON_LENGTH, "'json_data'"))
        return self.data(json_data)


@Packet.register
class AdminPing(Packet):
    packet_id = 7
    fields = ['payload']

    def encode(self, payload: int):
        self.write_uint(payload)

    def decode(self) -> Tuple[int]:
        payload, = self.read_uint()
        return self.data(payload)

