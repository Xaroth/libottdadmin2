#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from collections import namedtuple
from datetime import datetime
from typing import Tuple, Dict

from libottdadmin2.constants import NETWORK_NAME_LENGTH, NETWORK_REVISION_LENGTH, NETWORK_HOSTNAME_LENGTH, \
    NETWORK_CLIENT_NAME_LENGTH, NETWORK_COMPANY_NAME_LENGTH, NETWORK_CHAT_LENGTH, NETWORK_RCONCOMMAND_LENGTH, \
    NETWORK_GAMESCRIPT_JSON_LENGTH
from libottdadmin2.enums import ErrorCode, CompanyRemoveReason, Action, DestType, Landscape, Language, Colour
from libottdadmin2.packets.base import Packet, check_length, check_tuple_length
from libottdadmin2.packets.admin import AdminGamescript, AdminPing, AdminRcon
from libottdadmin2.util import gamedate_to_datetime, datetime_to_gamedate


@Packet.register
class ServerFull(Packet):
    packet_id = 100


@Packet.register
class ServerBanned(Packet):
    packet_id = 101


@Packet.register
class ServerError(Packet):
    packet_id = 102
    fields = ['errorcode']

    def encode(self, errorcode: ErrorCode):
        self.write_byte(ErrorCode(errorcode))

    def decode(self) -> Tuple[ErrorCode]:
        errorcode, = self.read_byte()
        return self.data(ErrorCode(errorcode))


@Packet.register
class ServerProtocol(Packet):
    packet_id = 103
    fields = ['version', 'settings']

    def encode(self, version: int, settings: Dict[int, int]):
        self.write_byte(version)
        for key, val in sorted(settings.items()):
            self.write_bool(True)
            self.write_ushort(key)
            self.write_ushort(val)
        self.write_bool(False)

    def decode(self) -> Tuple[int, Dict[int, int]]:
        version, _next = self.read_data(['byte', 'bool'])
        settings = {}
        while bool(_next):
            key, val, _next = self.read_data(['ushort', 'ushort', 'bool'])
            settings[key] = val
        return self.data(version, settings)


@Packet.register
class ServerWelcome(Packet):
    packet_id = 104
    fields = ['name', 'version', 'dedicated', 'map', 'seed', 'landscape', 'startdate', 'x', 'y']

    # noinspection PyShadowingBuiltins
    def encode(self, name: str, version: str, dedicated: bool, map: str, seed: int, landscape: Landscape,
               startdate: datetime, x: int, y: int):
        self.write_str(check_length(name, NETWORK_NAME_LENGTH, "'name'"),
                       check_length(version, NETWORK_REVISION_LENGTH, "'version'"))
        self.write_bool(dedicated)
        self.write_str(check_length(map, NETWORK_NAME_LENGTH, "'map'"))
        self.write_uint(seed)
        self.write_byte(Landscape(landscape))
        self.write_uint(datetime_to_gamedate(startdate))
        self.write_ushort(x, y)

    def decode(self) -> Tuple[str, str, bool, str, int, Landscape, datetime, int, int]:
        name, version = self.read_str(2)
        dedicated, = self.read_bool()
        _map, = self.read_str()
        seed, landscape, startdate, x, y = self.read_data(['uint', 'byte', 'uint', 'ushort', 'ushort'])
        return self.data(
            check_length(name, NETWORK_NAME_LENGTH, "'name'"),
            check_length(version, NETWORK_REVISION_LENGTH, "'version'"),
            dedicated,
            check_length(_map, NETWORK_NAME_LENGTH, "'map'"),
            seed,
            Landscape(landscape),
            gamedate_to_datetime(startdate),
            x,
            y,
        )


@Packet.register
class ServerNewGame(Packet):
    packet_id = 105


@Packet.register
class ServerShutdown(Packet):
    packet_id = 106


@Packet.register
class ServerDate(Packet):
    packet_id = 107
    fields = ['date']

    def encode(self, date: datetime):
        self.write_uint(datetime_to_gamedate(date))

    def decode(self) -> Tuple[datetime]:
        date, = self.read_uint()
        return self.data(gamedate_to_datetime(date))


@Packet.register
class ServerClientJoin(Packet):
    packet_id = 108
    fields = ['client_id']

    def encode(self, client_id: int):
        self.write_uint(client_id)

    def decode(self) -> Tuple[int]:
        client_id, = self.read_uint()
        return self.data(client_id)


@Packet.register
class ServerClientInfo(Packet):
    packet_id = 109
    fields = ['client_id', 'hostname', 'name', 'language', 'joindate', 'play_as']

    def encode(self, client_id: int, hostname: str, name: str, language: Language, joindate: datetime, play_as: int):
        self.write_uint(client_id)
        self.write_str(check_length(hostname, NETWORK_HOSTNAME_LENGTH, "'hostname'"),
                       check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"))
        self.write_byte(Language(language))
        self.write_uint(datetime_to_gamedate(joindate))
        self.write_byte(play_as)

    def decode(self) -> Tuple[int, str, str, Language, datetime, int]:
        client_id, = self.read_uint()
        hostname, name = self.read_str(2)
        language, joindate, play_as = self.read_data(['byte', 'uint', 'byte'])
        return self.data(
            client_id,
            check_length(hostname, NETWORK_HOSTNAME_LENGTH, "'hostname'"),
            check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"),
            Language(language),
            gamedate_to_datetime(joindate),
            play_as,
        )


@Packet.register
class ServerClientUpdate(Packet):
    packet_id = 110
    fields = ['client_id', 'name', 'play_as']

    def encode(self, client_id: int, name: str, play_as: int):
        self.write_uint(client_id)
        self.write_str(check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"))
        self.write_byte(play_as)

    def decode(self) -> Tuple[int, str, int]:
        client_id, = self.read_uint()
        name, = self.read_str()
        play_as, = self.read_byte()
        return self.data(client_id, check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"), play_as)


@Packet.register
class ServerClientQuit(ServerClientJoin):
    packet_id = 111


@Packet.register
class ServerClientError(Packet):
    packet_id = 112
    fields = ['client_id', 'errorcode']

    def encode(self, client_id: int, errorcode: ErrorCode):
        self.write_uint(client_id)
        self.write_byte(ErrorCode(errorcode))

    def decode(self) -> Tuple[int, ErrorCode]:
        client_id, errorcode = self.read_data(['uint', 'byte'])
        return self.data(client_id, ErrorCode(errorcode))


@Packet.register
class ServerCompanyNew(Packet):
    packet_id = 113
    fields = ['company_id']

    def encode(self, company_id: int):
        self.write_byte(company_id)

    def decode(self) -> Tuple[int]:
        company_id, = self.read_byte()
        return self.data(company_id)


@Packet.register
class ServerCompanyInfo(Packet):
    packet_id = 114
    fields = ['company_id', 'name', 'manager', 'colour', 'passworded', 'startyear', 'is_ai', 'bankruptcy_counter',
              'shareholders']

    def encode(self, company_id: int, name: str, manager: str, colour: Colour, passworded: bool, startyear: int,
               is_ai: bool, bankruptcy_counter: int, shareholders: Tuple[int, int, int, int]):
        self.write_byte(company_id)
        self.write_str(check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
                       check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"))
        self.write_byte(colour)
        self.write_bool(passworded)
        self.write_uint(startyear)
        self.write_bool(is_ai)
        self.write_byte(bankruptcy_counter)
        self.write_byte(*check_tuple_length(shareholders, 4, 4, "'shareholders'"))

    def decode(self) -> Tuple[int, str, str, Colour, bool, int, bool, int, Tuple[int, int, int, int]]:
        company_id, = self.read_byte()
        name, manager = self.read_str(2)
        colour, = self.read_byte()
        passworded, = self.read_bool()
        startyear, = self.read_uint()
        is_ai, = self.read_bool()
        bankruptcy_counter = None
        shareholders = None
        if self.has_available_data:
            bankruptcy_counter, = self.read_byte()
            shareholders = list(self.read_byte(4))
        return self.data(
            company_id,
            check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
            check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"),
            Colour(colour),
            passworded,
            startyear,
            is_ai,
            bankruptcy_counter,
            check_tuple_length(shareholders, 4, 4, "'shareholders'"),
        )


@Packet.register
class ServerCompanyUpdate(Packet):
    packet_id = 115
    fields = ['company_id', 'name', 'manager', 'colour', 'passworded', 'bankruptcy_counter', 'shareholders']

    def encode(self, company_id: int, name: str, manager: str, colour: Colour, passworded: bool,
               bankruptcy_counter: int, shareholders: Tuple[int, int, int, int]):
        self.write_byte(company_id)
        self.write_str(check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
                       check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"))
        self.write_byte(Colour(colour))
        self.write_bool(passworded)
        self.write_byte(bankruptcy_counter)
        self.write_byte(*check_tuple_length(shareholders, 4, 4, "'shareholders'"))

    def decode(self) -> Tuple[int, str, str, Colour, bool, int, Tuple[int, int, int, int]]:
        company_id, = self.read_byte()
        name, manager = self.read_str(2)
        colour, = self.read_byte()
        passworded, = self.read_bool()
        bankruptcy_counter, = self.read_byte()
        shareholders = list(self.read_byte(4))
        return self.data(
            company_id,
            check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
            check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"),
            colour,
            passworded,
            bankruptcy_counter,
            check_tuple_length(shareholders, 4, 4, "'shareholders'"),
        )


@Packet.register
class ServerCompanyRemove(Packet):
    packet_id = 116
    fields = ['company_id', 'reason']

    def encode(self, company_id: int, reason: CompanyRemoveReason):
        self.write_byte(company_id, CompanyRemoveReason(reason))

    def decode(self) -> Tuple[int, CompanyRemoveReason]:
        company_id, reason = self.read_byte(2)
        return self.data(company_id, CompanyRemoveReason(reason))


ServerCompanyEconomyHistory = namedtuple('ServerCompanyEconomyHistory', ['value', 'performance', 'delivered'])


@Packet.register
class ServerCompanyEconomy(Packet):
    packet_id = 117
    fields = ['company_id', 'money', 'current_loan', 'income', 'delivered', 'history']

    def encode(self, company_id: int, money: int, current_loan: int, income: int, delivered: int,
               history: Tuple[ServerCompanyEconomyHistory, ServerCompanyEconomyHistory]):

        self.write_byte(company_id)
        self.write_longlong(money, current_loan, income)
        self.write_ushort(delivered)
        history = [ServerCompanyEconomyHistory(*x) for x in check_tuple_length(history, 2, 2, "'history'")]
        for item in history:
            self.write_longlong(item.value)
            self.write_ushort(item.performance, item.delivered)

    def decode(self) -> Tuple[int, int, int, int, int, Tuple[ServerCompanyEconomyHistory, ServerCompanyEconomyHistory]]:
        company_id, = self.read_byte()
        money, current_loan, income = self.read_longlong(3)
        delivered_now, = self.read_ushort()
        history = [ServerCompanyEconomyHistory(*self.read_longlong(), *self.read_ushort(2)) for _ in range(2)]
        return self.data(
            company_id,
            money,
            current_loan,
            income,
            delivered_now,
            check_tuple_length(history, 2, 2, "'history'"),
        )


ServerCompanyStatsStats = namedtuple('ServerCompanyStatsStats', ['train', 'lorry', 'bus', 'plane', 'ship'])


@Packet.register
class ServerCompanyStats(Packet):
    packet_id = 118
    fields = ['company_id', 'vehicles', 'stations']

    def encode(self, company_id: int, vehicles: ServerCompanyStatsStats, stations: ServerCompanyStatsStats):
        self.write_byte(company_id)
        self.write_ushort(*ServerCompanyStatsStats(*vehicles))
        self.write_ushort(*ServerCompanyStatsStats(*stations))

    def decode(self) -> Tuple[int, ServerCompanyStatsStats, ServerCompanyStatsStats]:
        company_id, = self.read_byte()
        vehicles = ServerCompanyStatsStats(*self.read_ushort(5))
        stations = ServerCompanyStatsStats(*self.read_ushort(5))
        return self.data(company_id, vehicles, stations)


@Packet.register
class ServerChat(Packet):
    packet_id = 119
    fields = ['action', 'type', 'client_id', 'message', 'extra']

    # noinspection PyShadowingBuiltins
    def encode(self, action: Action, type: DestType, client_id: int, message: str, extra: int):
        self.write_byte(action, type)
        self.write_uint(client_id)
        self.write_str(check_length(message, NETWORK_CHAT_LENGTH, "'message'"))
        self.write_ulonglong(extra)

    def decode(self) -> Tuple[Action, DestType, int, str, int]:
        action, _type = self.read_byte(2)
        client_id, = self.read_uint()
        message, = self.read_str()
        extra, = self.read_ulonglong()
        return self.data(Action(action), DestType(_type), client_id,
                         check_length(message, NETWORK_CHAT_LENGTH, "'message'"), extra)


@Packet.register
class ServerRcon(Packet):
    packet_id = 120
    fields = ['colour', 'result']

    def encode(self, colour: Colour, result: str):
        self.write_ushort(Colour(colour))
        self.write_str(check_length(result, NETWORK_RCONCOMMAND_LENGTH, "'result'"))

    def decode(self) -> Tuple[Colour, str]:
        colour, = self.read_ushort()
        result, = self.read_str()
        return self.data(colour, check_length(result, NETWORK_RCONCOMMAND_LENGTH, "'result'"))


@Packet.register
class ServerConsole(Packet):
    packet_id = 121
    fields = ['origin', 'message']

    def encode(self, origin: str, message: str):
        # The maximum length for origin and message is not known. For sanity we stick to
        #  NETWORK_GAMESCRIPT_JSON_LENGTH as that is closest to SEND_MTU
        self.write_str(check_length(origin, NETWORK_GAMESCRIPT_JSON_LENGTH, "'origin'"),
                       check_length(message, NETWORK_GAMESCRIPT_JSON_LENGTH, "'message'"))

    def decode(self) -> Tuple[str, str]:
        # The maximum length for origin and message is not known. For sanity we stick to
        #  NETWORK_GAMESCRIPT_JSON_LENGTH as that is closest to SEND_MTU
        origin, message = self.read_str(2)
        return self.data(check_length(origin, NETWORK_GAMESCRIPT_JSON_LENGTH, "'origin'"),
                         check_length(message, NETWORK_GAMESCRIPT_JSON_LENGTH, "'message'"))


@Packet.register
class ServerCmdNames(Packet):
    packet_id = 122
    fields = ['commands']

    def encode(self, commands: Dict[int, str]):
        # Falling back to NETWORK_NAME_LENGTH as CmdNames doesn't have a max length defined
        for _id, name in sorted(commands.items()):
            self.write_bool(True)
            self.write_ushort(_id)
            self.write_str(check_length(name, NETWORK_NAME_LENGTH, "'name'"))
        self.write_bool(False)

    def decode(self) -> Tuple[Dict[int, str]]:
        commands = {}
        _next, = self.read_bool()
        while bool(_next):
            _id, name, _next = self.read_data(['ushort', str, bool])
            commands[_id] = check_length(name, NETWORK_NAME_LENGTH, "'name'")
        return self.data(commands)


@Packet.register
class ServerCmdLogging(Packet):
    packet_id = 123
    fields = ['client_id', 'company_id', 'command_id', 'param1', 'param2', 'tile', 'text', 'frame']

    def encode(self, client_id: int, company_id: int, command_id: int, param1: int, param2: int, tile: int,
               text: str, frame: int):
        # TODO: Figure out the max length for `text`
        self.write_uint(client_id)
        self.write_byte(company_id)
        self.write_ushort(command_id)
        self.write_uint(param1, param2, tile)
        self.write_str(text)
        self.write_uint(frame)

    def decode(self) -> Tuple[int, int, int, int, int, int, str, int]:
        client_id, company_id, command_id = self.read_data(['uint', 'byte', 'ushort'])
        param1, param2, tile = self.read_uint(3)
        text, = self.read_str()
        frame, = self.read_uint()
        return self.data(
            client_id,
            company_id,
            company_id,
            param1,
            param2,
            tile,
            text,
            frame,
        )


@Packet.register
class ServerGamescript(AdminGamescript):
    packet_id = 124


@Packet.register
class ServerRconEnd(AdminRcon):
    packet_id = 125


@Packet.register
class ServerPong(AdminPing):
    packet_id = 126
