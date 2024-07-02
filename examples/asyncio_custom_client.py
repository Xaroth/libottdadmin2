import argparse
import asyncio
import logging

from libottdadmin2.client.tracking import TrackingMixIn
from libottdadmin2.client.asyncio import OttdAdminProtocol
from libottdadmin2.constants import NETWORK_ADMIN_PORT

parser = argparse.ArgumentParser(description='Connect to OpenTTD via asyncio')
parser.add_argument("--password", help="The password to use for authentication")
parser.add_argument("--secret-key", help="The secret key for authentication")
parser.add_argument("--use-insecure-join", action='store_true',
    help="Enables joining OpenTTD servers version 14 and lower using an insecure protocol")
parser.add_argument('--host', default='127.0.0.1', help="The host to connect to")
parser.add_argument('--port', default=NETWORK_ADMIN_PORT, type=int, help="The port to connect to")

logging.basicConfig(level=logging.DEBUG)


class Client(TrackingMixIn, OttdAdminProtocol):
    pass


if __name__ == "__main__":
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(Client.connect(loop=loop, host=args.host, port=args.port,
                                                    password=args.password,
                                                    secret_key=args.secret_key,
                                                    use_insecure_join=args.use_insecure_join))
    loop.run_until_complete(client.client_active)
