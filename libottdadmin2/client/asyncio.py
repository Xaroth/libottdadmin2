#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

import asyncio
from typing import Optional

from libottdadmin2.client.common import OttdClientMixIn
from libottdadmin2.constants import NETWORK_ADMIN_PORT
from libottdadmin2.packets import Packet
from libottdadmin2.util import loggable


@loggable
class OttdAdminProtocol(OttdClientMixIn, asyncio.Protocol):
    # noinspection PyUnusedLocal
    def __init__(self, loop, password: Optional[str] = None, user_agent: Optional[str] = None,
                 version: Optional[str] = None, **kwargs):
        self.loop = loop
        self._buffer = b''
        self.client_active = asyncio.Future()
        self.transport = None
        self.peername = None

        self.configure(password=password, user_agent=user_agent, version=version)

    def _close(self):
        self.transport.close()
        if not self.client_active.done():
            self.client_active.set_result(True)

    def connection_lost(self, exc: Optional[Exception] = None) -> None:
        self.log.info("Connection lost to %s:%d", self.peername[0], self.peername[1])
        self._close()
        super().connection_lost(exc)

    def connection_closed(self) -> None:
        self.log.info("Connection closed to %s:%d", self.peername[0], self.peername[1])
        self._close()

    def send_packet(self, packet: Packet) -> None:
        self.transport.write(packet.write_to_buffer())

    @classmethod
    async def connect(cls, *, loop: asyncio.AbstractEventLoop = None, host: str = None, port: int = None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = NETWORK_ADMIN_PORT
        transport, protocol = await loop.create_connection(lambda: cls(loop, **kwargs), host, port)
        return protocol


__all__ = [
    'OttdAdminProtocol',
]
