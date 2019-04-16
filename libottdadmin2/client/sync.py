#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

# noinspection PyProtectedMember
from selectors import DefaultSelector, _BaseSelectorImpl, EVENT_READ
import socket
from typing import Union, Optional

from libottdadmin2.client.common import OttdClientMixIn
from libottdadmin2.constants import SEND_MTU
from libottdadmin2.packets import Packet
from libottdadmin2.util import loggable


@loggable
class OttdSocket(OttdClientMixIn, socket.socket):
    def __init__(self, password: Optional[str] = None, user_agent: Optional[str] = None, version: Optional[str] = None):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.peername = None
        self._connected = False
        self._last_error = None
        self._buffer = b''
        self._selector = None  # Type: Optional[_BaseSelectorImpl]
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

    def connection_lost(self, exc: Optional[Exception] = None) -> None:
        self.log.info("Connection lost to %s:%d", self.peername[0], self.peername[1])
        self.close()
        self._connected = False

    def connection_closed(self):
        self.log.info("Connection closed to %s:%d", self.peername[0], self.peername[1])
        self._connected = False
        self.close()

    def close(self) -> None:
        super().close()
        self._connected = False
        if self._selector:
            self._selector.unregister(self)
            self._selector = None

    def send_packet(self, packet: Packet):
        try:
            self.sendall(packet.write_to_buffer())
        except socket.error as e:
            self._last_error = e
            self.connection_lost(e)

    def register_to_selector(self, selector: _BaseSelectorImpl):
        # noinspection PyUnusedLocal
        def _read(conn: OttdSocket, mask):
            data = conn.recv(SEND_MTU)
            if data:
                conn.data_received(data)
            else:
                conn.connection_lost(exc=None)

        self._selector = selector
        selector.register(self, EVENT_READ, _read)


__all__ = [
    'DefaultSelector',
    'OttdSocket',
]
