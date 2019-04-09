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

    def connection_lost(self, exc: Optional[Exception] = None) -> None:
        self.log.info("Connection lost to %s:%d", self.peername[0], self.peername[1])
        self.transport.close()
        if not self.client_active.done():
            self.client_active.set_result(True)
        super().connection_lost(exc)

    def connection_closed(self) -> None:
        self.log.info("Connection closed to %s:%d", self.peername[0], self.peername[1])
        self.transport.close()
        if not self.client_active.done():
            self.client_active.set_result(True)

    def send_packet(self, packet: Packet) -> None:
        self.transport.write(packet.write_to_buffer())


async def connect(*, protocol: asyncio.Protocol = None, loop: asyncio.AbstractEventLoop = None, host: str = None,
                  port: int = None, **kwargs):
    if loop is None:
        loop = asyncio.get_event_loop()
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = NETWORK_ADMIN_PORT
    if protocol is None:
        protocol = OttdAdminProtocol
    _, protocol = await loop.create_connection(lambda: protocol(loop, **kwargs), host, port)
    return protocol


__all__ = [
    'OttdAdminProtocol',
    'connect',
]
