import argparse
import asyncio
import logging

from libottdadmin2.client.asyncio import connect
from libottdadmin2.constants import NETWORK_ADMIN_PORT

parser = argparse.ArgumentParser(description='Connect to OpenTTD via asyncio')
parser.add_argument('--password', default='123qwe', help="The password to connect with")
parser.add_argument('--host', default='127.0.0.1', help="The host to connect to")
parser.add_argument('--port', default=NETWORK_ADMIN_PORT, type=int, help="The port to connect to")

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(connect(loop=loop, host=args.host, port=args.port, password=args.password))
    loop.run_until_complete(client.client_active)
