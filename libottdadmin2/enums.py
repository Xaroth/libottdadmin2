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
    DARK_BLUE = 0x00
    PALE_GREEN = 0x01
    PINK = 0x02
    YELLOW = 0x03
    RED = 0x04
    LIGHT_BLUE = 0x05
    GREEN = 0x06
    DARK_GREEN = 0x07
    BLUE = 0x08
    CREAM = 0x09
    MAUVE = 0x0A
    PURPLE = 0x0B
    ORANGE = 0x0C
    BROWN = 0x0D
    GREY = 0x0E
    WHITE = 0x0F
    END = 0x10
    INVALID = 0xFF


class Landscape(IntEnum):
    TEMPERATE = 0x00
    ARCTIC = 0x01
    TROPIC = 0x02
    TOYLAND = 0x03


class Language(IntEnum):
    ANY = 0x00
    ENGLISH = 0x01
    GERMAN = 0x02
    FRENCH = 0x03
    BRAZILIAN = 0x04
    BULGARIAN = 0x05
    CHINESE = 0x06
    CZECH = 0x07
    DANISH = 0x08
    DUTCH = 0x09
    ESPERANTO = 0x0A
    FINNISH = 0x0B
    HUNGARIAN = 0x0C
    ICELANDIC = 0x0D
    ITALIAN = 0x0E
    JAPANESE = 0x0F
    KOREAN = 0x10
    LITHUANIAN = 0x11
    NORWEGIAN = 0x12
    POLISH = 0x13
    PORTUGUESE = 0x14
    ROMANIAN = 0x15
    RUSSIAN = 0x16
    SLOVAK = 0x17
    SLOVENIAN = 0x18
    SPANISH = 0x19
    SWEDISH = 0x1A
    TURKISH = 0x1B
    UKRAINIAN = 0x1C
    AFRIKAANS = 0x1D
    CROATIAN = 0x1E
    CATALAN = 0x1F
    ESTONIAN = 0x20
    GALICIAN = 0x21
    GREEK = 0x22
    LATVIAN = 0x23
    COUNT = 0x24
