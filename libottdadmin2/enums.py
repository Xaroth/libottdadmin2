#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from enum import IntEnum, IntFlag
from itertools import chain


class Status(IntEnum):
    INACTIVE = 0x00  # The admin is not connected nor active.
    ACTIVE = 0x01  # The admin is active.
    _END = 0x02  # Must ALWAYS be on the end of this list!! (period)


class UpdateType(IntEnum):
    DATE = 0x00  # Updates about the date of the game.
    CLIENT_INFO = 0x01  # Updates about the information of clients.
    COMPANY_INFO = 0x02  # Updates about the generic information of companies.
    COMPANY_ECONOMY = 0x03  # Updates about the economy of companies.
    COMPANY_STATS = 0x04  # Updates about the statistics of companies.
    CHAT = 0x05  # The admin would like to have chat messages.
    CONSOLE = 0x06  # The admin would like to have console messages.
    NAMES = 0x07  # The admin would like a list of all DoCommand names.
    LOGGING = 0x08  # The admin would like to have DoCommand information.
    GAMESCRIPT = 0x09  # The admin would like to have gamescript messages.
    _END = 0x0A  # Must ALWAYS be on the end of this list!! (period)


class UpdateFrequency(IntFlag):
    POLL = 0x01  # The admin can poll this.
    DAILY = 0x02  # The admin gets information about this on a daily basis.
    WEEKLY = 0x04  # The admin gets information about this on a weekly basis.
    MONTHLY = 0x08  # The admin gets information about this on a monthly basis.
    QUARTERLY = 0x10  # The admin gets information about this on a quarterly basis.
    ANUALLY = 0x20  # The admin gets information about this on a yearly basis.
    AUTOMATIC = 0x40  # The admin gets information about this when it changes.


class CompanyRemoveReason(IntEnum):
    MANUAL = 0x00  # The company is manually removed.
    AUTOCLEAN = 0x01  # The company is removed due to autoclean.
    BANKRUPT = 0x02  # The company went belly-up.
    _END = 0x03  # Sentinel for end.


class VehicleType(IntEnum):
    TRAIN = 0x00
    LORRY = 0x01
    BUS = 0x02
    PLANE = 0x03
    SHIP = 0x04
    _END = 0x05


class ClientID(IntEnum):
    INVALID = 0x00  # Client is not part of anything
    SERVER = 0x01  # Servers always have this ID
    FIRST = 0x02  # The first client ID


class DestType(IntEnum):
    BROADCAST = 0x00  # Send message/notice to all clients (All)
    TEAM = 0x01  # Send message/notice to everyone playing the same company (Team)
    CLIENT = 0x02  # Send message/notice to only a certain client (Private)


class PollExtra(IntEnum):
    ALL = 0xFFFFFFFF


class ChatAction(IntEnum):
    SERVER_MESSAGE = 0x02
    CHAT = 0x03
    CHAT_COMPANY = 0x04
    CHAT_CLIENT = 0x05

class NonChatAction(IntEnum):
    JOIN = 0x00
    LEAVE = 0x01
    # 0x02 - 0x05 are found in ChatAction
    GIVE_MONEY = 0x06
    NAME_CHANGE = 0x07
    COMPANY_SPECTATOR = 0x08
    COMPANY_JOIN = 0x09
    COMPANY_NEW = 0x0A


# noinspection PyTypeChecker
Action = IntEnum('Action', [(i.name, i.value) for i in sorted(chain(ChatAction, NonChatAction))])


class ErrorCode(IntEnum):
    GENERAL = 0x00  # Try to use this one like never

    # Signals from clients
    DESYNC = 0x01
    SAVEGAME_FAILED = 0x02
    CONNECTION_LOST = 0x03
    ILLEGAL_PACKET = 0x04
    NEWGRF_MISMATCH = 0x05

    # Signals from servers
    NOT_AUTHORIZED = 0x06
    NOT_EXPECTED = 0x07
    WRONG_REVISION = 0x08
    NAME_IN_USE = 0x09
    WRONG_PASSWORD = 0x0A
    COMPANY_MISMATCH = 0x0B  # Happens in CLIENT_COMMAND
    KICKED = 0x0C
    CHEATER = 0x0D
    FULL = 0x0E
    TOO_MANY_COMMANDS = 0x0F
    TIMEOUT_PASSWORD = 0x10
    TIMEOUT_COMPUTER = 0x11
    TIMEOUT_MAP = 0x12
    TIMEOUT_JOIN = 0x13
    _END = 0x14


class Colour(IntEnum):
    COLOUR_DARK_BLUE = 0x00
    COLOUR_PALE_GREEN = 0x01
    COLOUR_PINK = 0x02
    COLOUR_YELLOW = 0x03
    COLOUR_RED = 0x04
    COLOUR_LIGHT_BLUE = 0x05
    COLOUR_GREEN = 0x06
    COLOUR_DARK_GREEN = 0x07
    COLOUR_BLUE = 0x08
    COLOUR_CREAM = 0x09
    COLOUR_MAUVE = 0x0A
    COLOUR_PURPLE = 0x0B
    COLOUR_ORANGE = 0x0C
    COLOUR_BROWN = 0x0D
    COLOUR_GREY = 0x0E
    COLOUR_WHITE = 0x0F
    COLOUR_END = 0x10
    INVALID_COLOUR = 0xFF


class Landscape(IntEnum):
    TEMPERATE = 0x00
    ARCTIC = 0x01
    TROPIC = 0x02
    TOYLAND = 0x03

