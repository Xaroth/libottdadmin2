#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

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

from .packets import *
from .event import Event
from .adminconnection import AdminConnection

class AdminClient(AdminConnection):
    """
    The AdminClient class is a wrapper around the AdminConnection, allowing
    a user to create a bot more easy.
    """
    def __init_poll__(self):
        self._pollobj = poll()
        self._poll_registered = True
        self._pollobj.register(self.fileno(), POLLIN | POLLERR | POLLHUP | POLLPRI)

    def __deinit_poll__(self):
        if self._poll_registered:
            self._poll_registered = False
            self._pollobj.unregister(self.fileno())

    def poll(self, timeout = 1.0):
        """
        Polls the connection for a maximum of <timeout> seconds
        """
        events = self._pollobj.poll(timeout * POLL_MOD)
        packets = []
        for fileno, event in events:
            if fileno != self.fileno():
                continue
            if (event & POLLIN) or (event & POLLPRI):
                packets.append(self.recv_packet())
            elif (event & POLLERR) or (event & POLLHUP):
                self.force_disconnect()
        return packets


    def __init_events__(self):
        super(AdminClient, self).__init_events__()

        self.protocol_received = Event(self)
        self.map_info_received = Event(self)

    def __init_handlers__(self):
        super(AdminClient, self).__init_handlers__()
        self.disconnected += self.__deinit_poll__

        self.packet_recv += self.on_packet

        self.protocol_received += self.on_protocol_received
        self.map_info_received += self.on_map_info_received
        
        self._packet_handlers = {}
        self._packet_handlers[ServerProtocol.packetID] = self.protocol_received
        self._packet_handlers[ServerWelcome.packetID] = self.map_info_received

    def __init__(self):
        super(AdminClient, self).__init__()
        self.__init_poll__()

        self.protocol_info = {}
        self.map_info = {}        

    def on_packet(self, packetType, data):
        """
        This is a generic handler for packets; it checks if the packetID
        is listed in self._packet_handlers, and if so, call that funntion
        with the data as param.

        Unknown packets should work the same, however, the user will receive
        the raw data, rather than decoded information
        """
        pid = packetType
        if not isinstance(pid, (int,long)):
            pid = packetType.packetID
        if pid in self._packet_handlers:
            self._packet_handlers[pid](data)

    def on_protocol_received(self, data):
        self.protocol_info = data

    def on_map_info_received(self, data):
        self.map_info = data


