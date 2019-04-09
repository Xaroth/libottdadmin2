import argparse
import logging

from libottdadmin2.client.tracking import TrackingMixIn
from libottdadmin2.client.sync import OttdSocket, DefaultSelector, reader_for_socket
from libottdadmin2.constants import NETWORK_ADMIN_PORT

parser = argparse.ArgumentParser(description='Connect to OpenTTD via asyncio')
parser.add_argument('--password', default='123qwe', help="The password to connect with")
parser.add_argument('--host', default='127.0.0.1', help="The host to connect to")
parser.add_argument('--port', default=NETWORK_ADMIN_PORT, type=int, help="The port to connect to")

logging.basicConfig(level=logging.DEBUG)


class Client(TrackingMixIn, OttdSocket):
    pass


if __name__ == "__main__":
    args = parser.parse_args()
    selector = DefaultSelector()
    client = Client(password=args.password)
    client.connect((args.host, args.port))
    client.setblocking(False)
    reader_for_socket(selector, client)

    while True:
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
