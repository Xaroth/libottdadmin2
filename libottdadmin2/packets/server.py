#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from collections import namedtuple
from datetime import datetime

from libottdadmin2.constants import NETWORK_NAME_LENGTH, NETWORK_REVISION_LENGTH, NETWORK_HOSTNAME_LENGTH, \
    NETWORK_CLIENT_NAME_LENGTH, NETWORK_COMPANY_NAME_LENGTH, NETWORK_CHAT_LENGTH, NETWORK_RCONCOMMAND_LENGTH, \
    NETWORK_GAMESCRIPT_JSON_LENGTH
from libottdadmin2.enums import ErrorCode, CompanyRemoveReason, Action, DestType, Landscape
from libottdadmin2.packets.base import Packet, check_length
from libottdadmin2.packets.admin import AdminGamescript, AdminPing
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

    def decode(self):
        errorcode, = self.read_byte()
        return self.data(ErrorCode(errorcode))


@Packet.register
class ServerProtocol(Packet):
    packet_id = 103
    fields = ['version', 'settings']

    def encode(self, version, settings):
        self.write_byte(version)
        for key, val in sorted(settings.items()):
            self.write_bool(True)
            self.write_ushort(key)
            self.write_ushort(val)
        self.write_bool(False)

    def decode(self):
        version, next = self.read_data(['byte', 'bool'])
        settings = {}
        while bool(next):
            key, val, next = self.read_data(['ushort', 'ushort', 'bool'])
            settings[key] = val
        return self.data(version, settings)


@Packet.register
class ServerWelcome(Packet):
    packet_id = 104
    fields = ['name', 'version', 'dedicated', 'map', 'seed', 'landscape', 'startdate', 'x', 'y']

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

    def decode(self):
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

    def encode(self, date):
        self.write_uint(datetime_to_gamedate(date))

    def decode(self):
        date, = self.read_uint()
        return self.data(gamedate_to_datetime(date))


@Packet.register
class ServerClientJoin(Packet):
    packet_id = 108
    fields = ['client_id']

    def encode(self, client_id):
        self.write_uint(client_id)

    def decode(self):
        client_id, = self.read_uint()
        return self.data(client_id)


@Packet.register
class ServerClientInfo(Packet):
    packet_id = 109
    fields = ['client_id', 'hostname', 'name', 'language', 'joindate', 'play_as']

    def encode(self, client_id, hostname, name, language, joindate, play_as):
        self.write_uint(client_id)
        self.write_str(check_length(hostname, NETWORK_HOSTNAME_LENGTH, "'hostname'"),
                       check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"))
        self.write_byte(language)
        self.write_uint(datetime_to_gamedate(joindate))
        self.write_byte(play_as)

    def decode(self):
        client_id, = self.read_uint()
        hostname, name = self.read_str(2)
        language, joindate, play_as = self.read_data(['byte', 'uint', 'byte'])
        return self.data(
            client_id,
            check_length(hostname, NETWORK_HOSTNAME_LENGTH, "'hostname'"),
            check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"),
            language,
            gamedate_to_datetime(joindate),
            play_as,
        )


@Packet.register
class ServerClientUpdate(Packet):
    packet_id = 110
    fields = ['client_id', 'name', 'play_as']

    def encode(self, client_id, name, play_as):
        self.write_uint(client_id)
        self.write_str(check_length(name, NETWORK_CLIENT_NAME_LENGTH, "'name'"))
        self.write_byte(play_as)

    def decode(self):
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

    def encode(self, client_id, errorcode: ErrorCode):
        self.write_uint(client_id)
        self.write_byte(ErrorCode(errorcode))

    def decode(self):
        client_id, errorcode = self.read_data(['uint', 'byte'])
        return self.data(client_id, ErrorCode(errorcode))


@Packet.register
class ServerCompanyNew(Packet):
    packet_id = 113
    fields = ['company_id']

    def encode(self, company_id):
        self.write_byte(company_id)

    def decode(self):
        company_id, = self.read_byte()
        return self.data(company_id)


@Packet.register
class ServerCompanyInfo(Packet):
    packet_id = 114
    fields = ['company_id', 'name', 'manager', 'colour', 'passworded', 'startyear', 'is_ai', 'bankrupcy_counter',
              'shareholders']

    def encode(self, company_id, name, manager, colour, passworded, startyear, is_ai, bankrupcy_counter, shareholders):
        self.write_byte(company_id)
        self.write_str(check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
                       check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"))
        self.write_byte(colour)
        self.write_bool(passworded)
        self.write_uint(startyear)
        self.write_bool(is_ai)
        if shareholders is not None or bankrupcy_counter is not None:
            self.write_byte(bankrupcy_counter)
            self.write_byte(*((shareholders + ([0] * 4))[0:4]))

    def decode(self):
        company_id, = self.read_byte()
        name, manager = self.read_str(2)
        colour, = self.read_byte()
        passworded, = self.read_bool()
        startyear, = self.read_uint()
        is_ai, = self.read_bool()
        bankrupcy_counter = None
        shareholders = None
        if self.has_available_data:
            bankrupcy_counter, = self.read_byte()
            shareholders = list(self.read_byte(4))
        return self.data(
            company_id,
            check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
            check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"),
            colour,
            passworded,
            startyear,
            is_ai,
            bankrupcy_counter,
            shareholders,
        )


@Packet.register
class ServerCompanyUpdate(Packet):
    packet_id = 115
    fields = ['company_id', 'name', 'manager', 'colour', 'passworded', 'bankrupcy_counter', 'shareholders']

    def encode(self, company_id, name, manager, colour, passworded, bankrupcy_counter, shareholders):
        self.write_byte(company_id)
        self.write_str(check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
                       check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"))
        self.write_byte(colour)
        self.write_bool(passworded)
        self.write_byte(bankrupcy_counter)
        self.write_byte(*((shareholders + ([0] * 4))[0:4]))

    def decode(self):
        company_id, = self.read_byte()
        name, manager = self.read_str(2)
        colour, = self.read_byte()
        passworded, = self.read_bool()
        bankrupcy_counter, = self.read_byte()
        shareholders = list(self.read_byte(4))
        return self.data(
            company_id,
            check_length(name, NETWORK_COMPANY_NAME_LENGTH, "'name'"),
            check_length(manager, NETWORK_COMPANY_NAME_LENGTH, "'manager'"),
            colour,
            passworded,
            bankrupcy_counter,
            shareholders,
        )


@Packet.register
class ServerCompanyRemove(Packet):
    packet_id = 116
    fields = ['company_id', 'reason']

    def encode(self, company_id, reason: CompanyRemoveReason):
        self.write_byte(company_id, CompanyRemoveReason(reason))

    def decode(self):
        company_id, reason = self.read_byte(2)
        return self.data(company_id, CompanyRemoveReason(reason))


@Packet.register
class ServerCompanyEconomy(Packet):
    packet_id = 117
    fields = ['company_id', 'money', 'current_loan', 'income', 'delivered', 'history']
    history = namedtuple('ServerCompanyEconomyHistory', ['value', 'performance', 'delivered'])

    def encode(self, company_id, money, current_loan, income, delivered, history):
        hist_extra = [self.history(0, 0, 0)] * 2

        self.write_byte(company_id)
        self.write_longlong(money, current_loan, income)
        self.write_ushort(delivered)
        for value, performance, delivered_hist in (history + hist_extra)[:2]:
            self.write_longlong(value)
            self.write_ushort(performance, delivered_hist)

    def decode(self):
        company_id, = self.read_byte()
        money, current_loan, income = self.read_longlong(3)
        delivered_now, = self.read_ushort()
        history = []
        for i in range(2):
            value, = self.read_longlong()
            performance, delivered = self.read_ushort(2)
            history.append(self.history(value, performance, delivered))
        return self.data(
            company_id,
            money,
            current_loan,
            income,
            delivered_now,
            history,
        )


@Packet.register
class ServerCompanyStats(Packet):
    packet_id = 118
    fields = ['company_id', 'vehicles', 'stations']
    stats = namedtuple('ServerCompanyStatsStats', ['train', 'lorry', 'bus', 'plane', 'ship'])

    def encode(self, company_id, vehicles, stations):
        self.write_byte(company_id)
        for train, lorry, bus, plane, ship in (vehicles, stations):
            self.write_ushort(train, lorry, bus, plane, ship)

    def decode(self):
        company_id, = self.read_byte()
        vehicles = self.stats(*self.read_ushort(5))
        stations = self.stats(*self.read_ushort(5))
        return self.data(company_id, vehicles, stations)


@Packet.register
class ServerChat(Packet):
    packet_id = 119
    fields = ['action', 'type', 'client_id', 'message', 'extra']

    def encode(self, action: Action, type: DestType, client_id, message, extra):
        self.write_byte(action, type)
        self.write_uint(client_id)
        self.write_str(check_length(message, NETWORK_CHAT_LENGTH, "'message'"))
        self.write_ulonglong(extra)

    def decode(self):
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

    def encode(self, colour, result):
        self.write_ushort(colour)
        self.write_str(check_length(result, NETWORK_RCONCOMMAND_LENGTH, "'result'"))

    def decode(self):
        colour, = self.read_ushort()
        result, = self.read_str()
        return self.data(colour, check_length(result, NETWORK_RCONCOMMAND_LENGTH, "'result'"))


@Packet.register
class ServerConsole(Packet):
    packet_id = 121
    fields = ['origin', 'message']

    def encode(self, origin, message):
        # Falling back to NETWORK_GAMESCRIPT_JSON_LENGTH as there's no restriction in max length
        # for console messages.
        self.write_str(origin, check_length(message, NETWORK_GAMESCRIPT_JSON_LENGTH, "'message'"))

    def decode(self):
        origin, message = self.read_str(2)
        return self.data(origin, check_length(message, NETWORK_GAMESCRIPT_JSON_LENGTH, "'message'"))


@Packet.register
class ServerCmdNames(Packet):
    packet_id = 122
    fields = ['commands']

    def encode(self, commands):
        # Falling back to NETWORK_NAME_LENGTH as CmdNames doesn't have a max length defined
        for _id, name in sorted(commands.items()):
            self.write_bool(True)
            self.write_ushort(_id)
            self.write_str(check_length(name, NETWORK_NAME_LENGTH, "'name'"))
        self.write_bool(False)

    def decode(self):
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

    def encode(self, client_id, company_id, command_id, param1, param2, tile, text, frame):
        # TODO: Figure out the max length for `text`
        self.write_uint(client_id)
        self.write_byte(company_id)
        self.write_ushort(command_id)
        self.write_uint(param1, param2, tile)
        self.write_str(text)
        self.write_uint(frame)

    def decode(self):
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
class ServerRconEnd(Packet):
    packet_id = 125
    fields = ['command']

    def encode(self, command):
        self.write_str(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))

    def decode(self):
        command, = self.read_str()
        return self.data(check_length(command, NETWORK_RCONCOMMAND_LENGTH, "'command'"))


@Packet.register
class ServerPong(AdminPing):
    packet_id = 126
