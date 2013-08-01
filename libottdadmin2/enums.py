#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

class EnumHelper(object):
    is_flag = False
    __build = False
    __dict  = None
    __rdict = None
    __max   = None
    __min   = None

    @classmethod
    def _build(self):
        if self.__build:
            return
        self.__build = True
        self.__dict  = {}
        self.__rdict = {}

        for item in dir(self):
            if item.upper() != item:
                continue
            if item.startswith('_'):
                continue
            value = getattr(self, item, None)
            self.__dict[item] = value
            self.__rdict[value] = item
        items = sorted(self.__rdict.keys())
        if len(items) > 0:
            self.__max = items[-1]
            self.__min = items[0]

    @classmethod
    def is_valid(self, value):
        self._build()
        if self.is_flag:
            return value >= 0 and value < self.__max * 2
        else:
            return value in self.__rdict

    @classmethod
    def get_name(self, value):
        return self.__rdict.get(value, None)

    @classmethod
    def get_from_name(self, name):
        return self.__dict.get(name, None)

class Status(EnumHelper):
    INACTIVE            = 0x00  #< The admin is not connected nor active.
    ACTIVE              = 0x01  #< The admin is active.
    _END                = 0x02  #< Must ALWAYS be on the end of this list!! (period)

class UpdateType(EnumHelper):
    DATE                = 0x00  #< Updates about the date of the game.
    CLIENT_INFO         = 0x01  #< Updates about the information of clients.
    COMPANY_INFO        = 0x02  #< Updates about the generic information of companies.
    COMPANY_ECONOMY     = 0x03  #< Updates about the economy of companies.
    COMPANY_STATS       = 0x04  #< Updates about the statistics of companies.
    CHAT                = 0x05  #< The admin would like to have chat messages.
    CONSOLE             = 0x06  #< The admin would like to have console messages.
    NAMES               = 0x07  #< The admin would like a list of all DoCommand names.
    LOGGING             = 0x08  #< The admin would like to have DoCommand information.
    GAMESCRIPT          = 0x09  #< The admin would like to have gamescript messages.
    _END                = 0x0A  #< Must ALWAYS be on the end of this list!! (period)

class UpdateFrequency(EnumHelper):
    is_flag             = True

    POLL                = 0x01  #< The admin can poll this.
    DAILY               = 0x02  #< The admin gets information about this on a daily basis.
    WEEKLY              = 0x04  #< The admin gets information about this on a weekly basis.
    MONTHLY             = 0x08  #< The admin gets information about this on a monthly basis.
    QUARTERLY           = 0x10  #< The admin gets information about this on a quarterly basis.
    ANUALLY             = 0x20  #< The admin gets information about this on a yearly basis.
    AUTOMATIC           = 0x40  #< The admin gets information about this when it changes.

class CompanyRemoveReason(EnumHelper):
    MANUAL              = 0x00  #< The company is manually removed.
    AUTOCLEAN           = 0x01  #< The company is removed due to autoclean.
    BANKRUPT            = 0x02  #< The company went belly-up.
    _END                = 0x03  #< Sentinel for end.

class VehicleType(EnumHelper):
    TRAIN               = 0x00
    LORRY               = 0x01
    BUS                 = 0x02
    PLANE               = 0x03
    SHIP                = 0x04
    _END                = 0x05
    
class ClientID(EnumHelper):
    INVALID             = 0x00  #< Client is not part of anything
    SERVER              = 0x01  #< Servers always have this ID
    FIRST               = 0x02  #< The first client ID

class DestType(EnumHelper):
    BROADCAST           = 0x00  #< Send message/notice to all clients (All)
    TEAM                = 0x01  #< Send message/notice to everyone playing the same company (Team)
    CLIENT              = 0x02  #< Send message/notice to only a certain client (Private)

class Action(EnumHelper):
    JOIN                = 0x00
    LEAVE               = 0x01
    SERVER_MESSAGE      = 0x02
    CHAT                = 0x03
    CHAT_COMPANY        = 0x04
    CHAT_CLIENT         = 0x05
    GIVE_MONEY          = 0x06
    NAME_CHANGE         = 0x07
    COMPANY_SPECTATOR   = 0x08
    COMPANY_JOIN        = 0x09
    COMPANY_NEW         = 0x0A
