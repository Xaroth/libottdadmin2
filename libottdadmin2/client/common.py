#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from asyncio import transports
from typing import Tuple, Any, Optional

from libottdadmin2.packets import AdminJoin, Packet, AdminQuit
from libottdadmin2.util import loggable, camel_to_snake


@loggable
class OttdClientMixIn:
    _buffer = None  # Type: bytes
    _password = None  # Type: Optional[str]
    _user_agent = None  # Type: Optional[str]
    _version = None  # Type: Optional[str]
    transport = None  # Type: Optional[transports.Transport]
    peername = None  # Type: Tuple[str, int]

    def configure(self, password: Optional[str] = None, user_agent: Optional[str] = None,
                  version: Optional[str] = None):
        from libottdadmin2 import VERSION
        self._password = password
        self._user_agent = user_agent or "libottdadmin2"
        self._version = version or VERSION

    def connection_made(self, transport: transports.Transport = None) -> None:
        if transport:
            self.transport = transport
            self.peername = transport.get_extra_info("peername")

        self.log.info("Connection made to %s:%d", self.peername[0], self.peername[1])

        if self._password:
            self.log.info("Automatically authenticating: %s@%s", self._user_agent, self._version)
            self.send_packet(AdminJoin.create(password=self._password, name=self._user_agent, version=self._version))

    def data_received(self, data: bytes) -> None:
        self._buffer += data
        while True:
            found, length, packet = Packet.extract(self._buffer)
            self._buffer = self._buffer[length:]
            if not found:
                break
            self.packet_received(packet, packet.decode())

    def packet_received(self, packet: Packet, data: Tuple[Any, ...]) -> None:
        self.log.debug("Packet received: %r", data)
        func_name = camel_to_snake(packet.__class__.__name__)
        handler = getattr(self, "on_%s" % func_name, None)
        if handler and callable(handler):
            # noinspection PyProtectedMember,PyUnresolvedReferences
            handler(**data._asdict())
        handler = getattr(self, "on_%s_raw" % func_name, None)
        if handler and callable(handler):
            handler(packet=packet, data=data)

    def connection_closed(self) -> None:
        pass

    def connection_lost(self, exc: Optional[Exception]) -> None:
        pass

    def send_packet(self, packet: Packet) -> None:
        raise NotImplemented()

    def disconnect(self) -> None:
        self.send_packet(AdminQuit.create())
        self.connection_closed()

    def on_server_shutdown(self):
        self.log.debug("Server is shutting down")
        self.connection_closed()


__all__ = [
    'OttdClientMixIn',
]
