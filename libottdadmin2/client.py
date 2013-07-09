#
# Helper imports:
#  This allows you to use the select.poll functionality 
#  ( http://docs.python.org/2/library/select.html#poll-objects )
#  While automatically using epoll if it's available.
#  .. Keep in mind to multiply the timeeout for poll.poll()
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

from libottdadmin2.packets import *
from libottdadmin2 import VERSION
from libottdadmin2.event import Event
from .util import LoggableObject

import socket

RETRIES = 3
VERSIONSTRING = "loa2-v%s" % VERSION
NAME = "LibOTTDAdmin"

class AdminConnection(socket.socket, LoggableObject):
    format_packetlen = Struct.create("H")
    format_packetid  = Struct.create("B")

    def __init_events__(self):
        self.connected = Event()
        self.disconnected = Event()
        self.packet_send = Event()        
        self.packet_recv = Event()

    def __init_handlers__(self):
        self.connected += self.on_connect
        self.disconnected += self.on_disconnect

    def __init__(self, password = None, retries = None, version = None, name = None):
        super(AdminConnection, self).__init__()
        self._retries    = retries or RETRIES
        self._version    = version or VERSIONSTRING
        self._name       = name    or NAME
        self._password   = password

        self._connected  = True
        self._must_retry = True

        self._last_host  = None
        self._last_port  = 3977
        self._last_error = None

        self.__init_events__()
        self.__init_handlers__()

    @property
    def is_connected(self):
        return self._connected

    def connect(self, server=None, port=None):
        if isinstance(server, tuple):
            server, port = server
        server = server or self._last_host
        port = port or self._last_port
        if server is None or port is None:
            raise ValueError("Host and/or port may not be None")

        self._last_host, self._last_port = server, port
        self._must_retry = True
        try:
            self.log.info("Connecting to: %s:%d", server, port)
            super(AdminConnection, self).connect((server, port))
            self._connected = True
            self.connected()
            return True
        except socket.error as e:
            self._last_error = e
            return False

    def disconnect(self):
        self.log.info("Disconnecting")
        self.send_packet(AdminQuit)
        self._must_retry = False
        self.force_disconnect()

    def on_disconnect(self):
        if self._must_retry:
            pass

    def on_connect(self):
        self.authenticate()

    def send_packet(self, packetType, **kwargs):
        try:
            packetType = send[packetType]
            self.packet_send(packetType, **kwargs)
            self.log.info("Sending packet of type: %s", str(packetType))
            self.log.debug("Data: '%r'", kwargs)
            return self.sendall(packetType(**kwargs))
        except socket.error as e:
            return self.force_disconnect(e)

    def force_disconnect(self, e = None):
        self.log.info("Forced disconnecting")
        if e:
            self._last_error = e
        self._connected = False
        try:
            self.close()
        except socket.error:
            pass
        self.disconnected()

    def recv_packet(self):
        plen = self.recv(self.format_packetlen.size)
        if plen is None:
            return self.force_disconnect()
        plen = self.format_packetlen.unpack_from(plen)[0]
        data = self.recv(plen - self.format_packetlen.size)
        if data is None:
            return self.force_disconnect()
        packetID = self.format_packetid.unpack_from(data)[0]
        data = data[self.format_packetid.size:]
        try:
            packet = receive[packetID]
            self.log.info("Received packet of type: %s", str(packet))
            data = packet(data)
            self.log.debug("Data: '%r'", data)
            self.packet_recv(packet, data)
            return (packet, data)
        except PacketNotFound as e:
            self.log.warning("Could not find packet with id %d", packetID)
            return self.force_disconnect(e)
        return None

    def authenticate(self, password = None, name = None, version = None):
        password = password or self._password
        name     = name     or self._name
        version  = version  or self._version
        if not password or not name or not version:
            return
        self.log.info("Authenticating")
        self.send_packet(AdminJoin, password=password, name=name, version=version)




