#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

#
# Parts of this is copied straight from client.py
#  This is done, because I want to re-design the way
#  I deal with incoming packets, without breaking
#  the API for the normal AdminClient.
#

#
# Helper imports:
#  This allows you to use the select.poll functionality 
#  ( http://docs.python.org/2/library/select.html#poll-objects )
#  While automatically using epoll if it's available.
#  .. Keep in mind to multiply the timeout for poll.poll()
#     with  POLL_MOD
#

USES_POLL = USES_EPOLL = False
try:
    from select import epoll as poll, EPOLLIN as POLLIN, \
                       EPOLLOUT as POLLOUT, EPOLLERR as POLLERR, \
                       EPOLLHUP as POLLHUP, EPOLLPRI as POLLPRI
    POLL_MOD   = 1.0
    USES_EPOLL = True
except ImportError:
    try:
        from select import poll, POLLIN, POLLOUT, POLLERR, POLLHUP, POLLPRI
        POLL_MOD   = 1000.0
        USES_POLL  = True
    except ImportError:
        pass

from .adminconnection import AdminConnection
from .packets import *
from .event import Event
from .enums import *

from functools import wraps
from collections import defaultdict

from datetime import datetime, timedelta
import time
import socket

def handles_packet(*items):
    packets = [x if isinstance(x, (int, long)) else x.packetID for x in items]
    def __inner(func):
        func.handles_packet = packets
        return func
    return __inner

class MappingObject(object):
    def __init__(self, kwargs = {}):
        self.update(kwargs, True)

    def update(self, kwargs = {}, set_null = False):
        for key, to in self._mapping:
            if not set_null and key not in kwargs:
                continue
            setattr(self, to, kwargs.get(key))

    def to_dict(self):
        return dict([(x, getattr(self, x, None)) for _, x in self._mapping])

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

class MapInfo(MappingObject):
    _mapping = [
        ('x', 'x'),
        ('y', 'y'),
        ('map_name', 'name'),
        ('landscape', 'landscape'),
        ('startyear', 'startyear'),
        ('seed', 'seed'),
    ]

class ServerInfo(MappingObject):
    _mapping = [
        ('version', 'version'),
        ('name', 'name'),
        ('dedicated', 'dedicated'),
    ]

class ProtocolInfo(MappingObject):
    _mapping = [
        ('version', 'version'),
        ('settings', 'settings'),
    ]

class ClientInfo(MappingObject):
    _mapping = [
        ('clientID', 'id'),
        ('name', 'name'),
        ('hostname', 'hostname'),
        ('language', 'language'),
        ('joindate', 'joindate'),
        ('play_as', 'play_as'),
    ]

class CompanyInfo(MappingObject):
    _mapping = [
        ('companyID', 'id'),
        ('name', 'name'),
        ('manager', 'manager'),
        ('colour', 'colour'),
        ('passworded', 'passworded'),
        ('startYear', 'startyear'),
        ('isAI', 'ai'),
        ('bankrupcyCounter', 'bankrupcyCounter'),
        ('shareholders', 'shareholders'),
    ]
    def __init__(self, *args, **kwargs):
        super(CompanyInfo, self).__init__(*args, **kwargs)
        self.vehicles = VehicleStats()
        self.stations = VehicleStats()
        self.economy  = CompanyEconomy()

class CompanyEconomy(MappingObject):
    _mapping = [
        ('money', 'money'),
        ('currentLoan', 'currentLoan'),
        ('income', 'income'),
        ('deliveredCargo', 'deliveredCargo'),
        ('history', 'history'),
    ]

class VehicleStats(MappingObject):
    _mapping = [
        ('train', 'train'),
        ('lorry', 'lorry'),
        ('bus', 'bus'),
        ('plane', 'plane'),
        ('ship', 'ship'),
    ]

class TrackingEvents(object):
    def __init__(self):
        self.connected      = Event()
        self.disconnected   = Event()

        self.shutdown       = Event()
        self.new_game       = Event()

        self.new_map        = Event()
        self.protocol       = Event()

        self.datechanged    = Event()

        self.clientinfo     = Event()
        self.clientjoin     = Event()
        self.clientupdate   = Event()
        self.clientquit     = Event()

        self.companyinfo    = Event()
        self.companynew     = Event()
        self.companyupdate  = Event()
        self.companyremove  = Event()
        self.companystats   = Event()
        self.companyeconomy = Event()

        self.chat           = Event()
        self.rcon           = Event()
        self.rconend        = Event()
        self.console        = Event()
        self.cmdlogging     = Event()

        self.pong           = Event()

class TrackingAdminClient(AdminConnection):
    _settable_args = AdminConnection._settable_args + ['timeout', 'poll_once']
    _timeout = 0.25
    _poll_once = False
    @property
    def timeout(self):
        return self._timeout
    @timeout.setter
    def timeout(self, value):
        self._timeout = float(value)
    @property
    def poll_once(self):
        return self._poll_once
    @poll_once.setter
    def poll_once(self, value):
        self._poll_once = bool(value)

    update_types = [
        (UpdateType.CLIENT_INFO,        UpdateFrequency.AUTOMATIC),
        (UpdateType.COMPANY_INFO,       UpdateFrequency.AUTOMATIC),
        (UpdateType.COMPANY_ECONOMY,    UpdateFrequency.MONTHLY),
        (UpdateType.COMPANY_STATS,      UpdateFrequency.MONTHLY),
        (UpdateType.CHAT,               UpdateFrequency.AUTOMATIC),
        (UpdateType.CONSOLE,            UpdateFrequency.AUTOMATIC),
        (UpdateType.DATE,               UpdateFrequency.DAILY),
    ]
    poll_types = [
        UpdateType.CLIENT_INFO,
        UpdateType.COMPANY_INFO,
        UpdateType.COMPANY_ECONOMY,
        UpdateType.COMPANY_STATS,
        UpdateType.DATE,
    ]

    def __init_poll__(self):
        self._pollobj = poll()
        self._poll_registered = True
        self._pollobj.register(self.fileno(), POLLIN | POLLERR | POLLHUP | POLLPRI)

    def __deinit_poll__(self, *args):
        if self._poll_registered:
            self._poll_registered = False
            try:
                self._pollobj.unregister(self.fileno())
            except socket.error as error:
                pass
            finally:
                self._pollobj = None

    def poll(self, timeout = None):
        """
        Polls the connection for a maximum of <timeout> seconds

        Returns False if the poll mechanism has been deconstructed, or
        when we are not (yet) connected to the server.
        Returns None if the connection has been lost.
        Returns a list of (PacketType, Data) for all packets received, 
        however, only one packet is read per poll call for now (this
        might change in the future)
        """
        if timeout is None:
            timeout = self.timeout
        if not self._poll_registered:
            return False
        if not self.is_connected:
            return False
        start = time.time()
        timeleft = timeout
        packets = []
        while timeleft > 0.0:
            events = self._pollobj.poll(timeleft * POLL_MOD)
            for fileno, event in events:
                if fileno != self.fileno():
                    continue
                if (event & POLLIN) or (event & POLLPRI):
                    packet = self.recv_packet()
                    if packet is None:
                        self.force_disconnect()
                        return None
                    packets.append(packet)
                elif (event & POLLERR) or (event & POLLHUP):
                    self.force_disconnect()
                    return packets
            taken = time.time() - start
            timeleft -= taken
            if self.poll_once:
                break
        return packets

    events = None

    pingrequests = {}

    def copy(self):
        obj = TrackingAdminClient(self.events)
        for prop in self._settable_args:
            setattr(obj, prop, getattr(self, prop, None))
        return obj

    def __init__(self, events = None):
        self.events = events
        super(TrackingAdminClient, self).__init__()
        self.__init_poll__()

        self.pingrequests = {}

    def __init_events__(self):
        #super(TrackingAdminClient, self).__init_events__()
        if self.events is None:
            self.events = TrackingEvents()

    def __init_handlers__(self):
        #super(TrackingAdminClient, self).__init_handlers__()

        self.packet_handlers = defaultdict(list)

        for func in dir(self):
            if func.startswith('__'):
                continue
            func = getattr(self, func)
            if not hasattr(func, 'handles_packet'):
                continue
            packets = list(func.handles_packet)
            for packetID in packets:
                self.packet_handlers[packetID].append(func)

    def disconnected(self, can_retry):
        self.__deinit_poll__()
        self.events.disconnected(can_retry)

    def connected(self):
        self.authenticate()
        self.events.connected()

    def packet_send(self, packetType, **packetData):
        self.handle_packet(packetType, packetData)

    def packet_recv(self, packetType, packetData):
        self.handle_packet(packetType, packetData)

    def handle_packet(self, packetType, packetData):
        pid = packetType
        if not isinstance(pid, (int,long)):
            pid = packetType.packetID

        for handler in self.packet_handlers[pid]:
            handler(**(packetData or {}))


    def ping(self):
        now = datetime.now()
        index = len(self.pingrequests.keys()) + 1
        self.pingrequests[index] = now
        self.send_packet(AdminPing, payload = index)

    @handles_packet(ServerPong)
    def _server_pong(self, payload):
        answer = datetime.now()
        if payload in self.pingrequests:
            start = self.pingrequests[payload]
            taken = answer - start
            del self.pingrequests[payload]
            self.events.pong(start, answer, taken)

    protocol = ProtocolInfo()

    @handles_packet(ServerProtocol)
    def _server_protocol(self, **kwargs):
        self.protocol = ProtocolInfo(kwargs)

        self.events.protocol(self.protocol)

        for updType, updFreq in self.update_types:
            self.send_packet(AdminUpdateFrequency, updateType = updType, updateFreq = updFreq) 

    mapinfo     = MapInfo()
    serverinfo  = ServerInfo()
    date        = datetime.min

    clients     = {}
    companies   = {}

    @handles_packet(ServerWelcome)
    def _server_welcome(self, **kwargs):
        self.mapinfo = MapInfo(kwargs)
        self.serverinfo = ServerInfo(kwargs)

        self.events.new_map(self.mapinfo, self.serverinfo)
        self.clients = {}
        self.companies = {255: CompanyInfo({
                'companyID': 255,
                'name': 'spectators',
                'manager': 'Spec Tator',
                'colour': 0,
                'passworded': False, 
                'startYear': (self.mapinfo.startyear or datetime.mine).year,
                'isAI': False,
            })}
        self.date = datetime.min
        for pollType in self.poll_types:
            self.send_packet(AdminPoll, pollType = pollType, extra = PollExtra.ALL)

    @handles_packet(ServerDate)
    def _server_date(self, date):
        self.date = date
        self.events.datechanged(date)

    @handles_packet(ServerShutdown)
    def _server_shutdown(self):
        self.events.shutdown()

    @handles_packet(ServerNewGame)
    def _server_new_game(self):
        self.events.new_game()

    @handles_packet(ServerClientInfo)
    def _server_client_info(self, **kwargs):
        client = ClientInfo(kwargs)
        self.clients[client.id] = client
        self.events.clientinfo(client)

    @handles_packet(ServerClientJoin)
    def _server_client_join(self, clientID):
        client = self.clients.get(clientID, clientID)
        self.events.clientjoin(client)

    @handles_packet(ServerClientUpdate)
    def _server_client_update(self, clientID, **kwargs):
        client = self.clients.get(clientID)
        if not client:
            return
        old = client.clone()
        client.update(kwargs)
        changed = [k for k, v in kwargs.items() if getattr(old, k, None) != v]
        self.events.clientupdate(old, client, changed)

    @handles_packet(ServerClientError, ServerClientQuit)
    def _server_client_remove(self, clientID, errorcode = None):
        client = self.clients.get(clientID, clientID)
        self.events.clientquit(client, errorcode)
        if clientID in self.clients:
            del self.clients[clientID]

    @handles_packet(ServerCompanyInfo)
    def _server_company_info(self, **kwargs):
        company = CompanyInfo(kwargs)
        self.companies[company.id] = company
        self.events.companyinfo(company)

    @handles_packet(ServerCompanyNew)
    def _server_company_new(self, companyID):
        company = self.companies.get(companyID, companyID)
        self.events.companynew(company)

    @handles_packet(ServerCompanyUpdate)
    def _server_company_update(self, companyID, **kwargs):
        company = self.companies.get(companyID)
        if not company:
            return
        old = company.clone()
        company.update(kwargs)
        changed = [k for k, v in kwargs.items() if getattr(old, k, None) != v]
        self.events.companyupdate(old, company, changed)

    @handles_packet(ServerCompanyRemove)
    def _server_company_remove(self, companyID, reason):
        company = self.companies.get(companyID, companyID)
        self.events.companyremove(company, reason)
        if companyID in self.companies:
            del self.companies[companyID]

    @handles_packet(ServerCompanyStats)
    def _server_company_stats(self, companyID, stats):
        company = self.companies.get(companyID)
        if not company:
            return
        company.vehicles.update(stats['vehicles'])
        company.stations.update(stats['stations'])
        self.events.companystats(company)

    @handles_packet(ServerCompanyEconomy)
    def _server_company_economy(self, companyID, **kwargs):
        company = self.companies.get(companyID)
        if not company:
            return
        company.economy.update(kwargs)
        self.events.companyeconomy(company)

    @handles_packet(ServerChat)
    def _server_chat(self, **kwargs):
        data = dict(kwargs.items())
        client = self.clients.get(data['clientID'], data['clientID'])
        data['client'] = client
        self.events.chat(**data)

    @handles_packet(ServerRcon)
    def _server_rcon(self, result, colour):
        self.events.rcon(result, colour)

    @handles_packet(ServerRconEnd)
    def _server_rcon_end(self, command):
        self.events.rconend(command)

    @handles_packet(ServerConsole)
    def _server_console(self, message, origin):
        self.events.console(message, origin)

    @handles_packet(ServerCmdLogging)
    def _server_cmd_logging(self, **kwargs):
        data = dict(kwargs.items())
        self.events.cmdlogging(**data)