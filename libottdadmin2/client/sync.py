#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from selectors import DefaultSelector, _BaseSelectorImpl, EVENT_READ
import socket
from typing import Union, Optional

from libottdadmin2.client.common import OttdClientMixIn
from libottdadmin2.constants import SEND_MTU
from libottdadmin2.packets import Packet


def reader_for_socket(selector: _BaseSelectorImpl, socket: socket.socket):
    def _read(conn, mask):
        data = conn.recv(SEND_MTU)
        if data:
            conn.data_received(data)
        else:
            selector.unregister(conn)
            conn.connection_lost()

    selector.register(socket, EVENT_READ, _read)


class OttdSocket(OttdClientMixIn, socket.socket):
    def __init__(self, password=None, user_agent=None, version=None):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.peername = None
        self._connected = False
        self._last_error = None
        self._buffer = b''
        self.configure(password=password, user_agent=user_agent, version=version)

    def connect(self, address: Union[tuple, str, bytes]) -> bool:
        try:
            self.peername = address
            super().connect(address)
            self._connected = True
        except socket.error as e:
            self._last_error = e
            self._connected = False

        self.connection_made()
        return self._connected

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.log.info("Connection lost to %s:%d", self.peername[0], self.peername[1])
        self.close()
        self._connected = False

    def connection_closed(self):
        self.log.info("Connection closed to %s:%d", self.peername[0], self.peername[1])
        self._connected = False
        self.close()

    def send_packet(self, packet: Packet):
        try:
            self.sendall(packet.write_to_buffer())
        except socket.error as e:
            self._last_error = e
            self.connection_lost(e)


__all__ = [
    'DefaultSelector',
    'reader_for_socket',
    'OttdSocket',
]
