from libottdadmin2.packets import *
from libottdadmin2 import VERSION
from libottdadmin2.event import Event
from .util import LoggableObject

from .constants import NETWORK_ADMIN_PORT

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

    def __init__(self):
        super(AdminConnection, self).__init__()
        self.version    = VERSIONSTRING
        self.name       = NAME
        self.password   = None

        self._connected = False

        self._host      = "127.0.0.1"
        self._port      = NETWORK_ADMIN_PORT
        self._last_error = None

        self.__init_events__()
        self.__init_handlers__()

    @property
    def is_connected(self):
        return self._connected

    @property
    def password(self):
        """
        Seeing passwords can be sensitive information,
        We'll only return True or False depending on whether or not a
        password has been set.
        """
        return True if self._password else False

    @password.setter
    def password(self, password):
        self._password = password

    @property
    def version(self):
        return self._version 

    @version.setter
    def version(self, value):
        self._version = value[:15]

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    def configure(self, **kwargs):
        """
        Configure this AdminConnection.

        Possible keyword arguments:
        - version : To set the version string
        - name    : To set the admin name
        - host    : To set the host to connect to
        - port    : To set the port to connect to
        - password: To set the password to use for authentication.
        """
        for arg in ['version', 'password', 'name', 'host', 'port']:
            if arg in kwargs:
                setattr(self, arg, kwargs[arg])

    def connect(self, server=None, port=None):
        """
        Connect to the OpenTTD Admin port.

        The following optional arguments are possible; if specified they will
        override the current set value for them:
        - host    : To set the host to connect to
        - port    : To set the port to connect to
        """
        if isinstance(server, tuple):
            server, port = server
        server = server or self.host
        port = port or self.port
        if server is None or port is None:
            raise ValueError("Host and/or port may not be None")

        self.host, self.port = server, port
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
        """
        Disconnect from the Admin port.

        This sends an AdminQuit packet to notify the server we are
        disconnecting, before closing the connection.
        """
        self.log.info("Disconnecting")
        self.send_packet(AdminQuit)
        self.force_disconnect(can_retry = False)

    def on_connect(self):
        self.authenticate()

    def send_packet(self, packetType, **kwargs):
        """
        Send a packet to the server.

        packetType is the packet class or the packet ID to send,
        keyword arguments passed will be passed to the packet to generate
        the data stream.

        Example:
        send_packet(AdminJoin, password=password, name=name, version=version).

        Note that all packets sent also cause the packet_sent event to fire.
        """
        try:
            packetType = send[packetType]
            self.packet_send(packetType, **kwargs)
            self.log.info("Sending packet of type: %s", str(packetType))
            self.log.debug("Data: '%r'", kwargs)
            return self.sendall(packetType(**kwargs))
        except socket.error as e:
            return self.force_disconnect(can_retry = True, error = e)

    def force_disconnect(self, can_retry = True, error = None):
        """
        Force an unclean disconnect of the connection.. this should only
        be called if the connection cannot be recovered (by being terminated by
        the server)
        """
        self.log.info("Forced disconnecting")
        if error:
            self._last_error = error
        self._connected = False
        try:
            self.close()
        except socket.error:
            pass
        self.disconnected(can_retry)

    def recv_packet(self):
        """
        Receives a packet from the server (or blocks until possible).

        Returns None if an error occurred (and as such, forced a disconnect).
        Returns (PacketClass, {decoded data}) if a packet was recognised.
        Returns (PacketID, stream_data) if a packet was not recognised.

        Note that all packets received cause the packet_recv event to fire.
        """
        plen = self.recv(self.format_packetlen.size)
        if plen is None or len(plen) < self.format_packetlen.size:
            return self.force_disconnect(can_retry = True)
        plen = self.format_packetlen.unpack_from(plen)[0]
        data = self.recv(plen - self.format_packetlen.size)
        if data is None or len(data) < (plen - self.format_packetlen.size):
            return self.force_disconnect(can_retry = True)
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
            return (packetID, data)
        return None

    def authenticate(self, password = None, name = None, version = None):
        """
        The following optional arguments are possible; if specified they will
        override the current set value for them:
        - password: To set the password to use for authentication.
        - version : To set the version string
        - name    : To set the admin name
        """
        password = password or self._password
        name     = name     or self.name
        version  = version  or self.version
        if not password or not name or not version:
            return
        self.password, self.name, self.version = password, name, version
        self.log.info("Authenticating")
        self.send_packet(AdminJoin, password=password, name=name, version=version)
