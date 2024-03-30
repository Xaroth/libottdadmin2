import argparse
import logging
from typing import Dict

from libottdadmin2.enums import Action, DestType, UpdateType, UpdateFrequency
from libottdadmin2.client.tracking import TrackingMixIn
from libottdadmin2.client.sync import OttdSocket, DefaultSelector
from libottdadmin2.constants import NETWORK_ADMIN_PORT

parser = argparse.ArgumentParser(description="Connect to OpenTTD via asyncio")
parser.add_argument("--password", help="The password to use for authentication")
parser.add_argument("--secret-key", help="The secret key for authentication")
parser.add_argument("--use-insecure-join", action='store_true',
    help="Enables joining OpenTTD servers version 14 and lower using an insecure protocol")
parser.add_argument("--host", default="127.0.0.1", help="The host to connect to")
parser.add_argument(
    "--port", default=NETWORK_ADMIN_PORT, type=int, help="The port to connect to"
)

logging.basicConfig(level=logging.DEBUG)


class Client(TrackingMixIn, OttdSocket):
    update_types = {
        **TrackingMixIn.update_types,
        **{
            UpdateType.CONSOLE: UpdateFrequency.AUTOMATIC,
            UpdateType.CHAT: UpdateFrequency.AUTOMATIC,
            UpdateType.NAMES: UpdateFrequency.POLL,
            UpdateType.LOGGING: UpdateFrequency.AUTOMATIC,
        },
    }
    commands = None

    def _reset(self) -> None:
        super()._reset()
        self.commands = {}

    def on_server_chat(
        self, action: Action, type: DestType, client_id: int, message: str, extra: int
    ):
        client = self.clients.get(client_id, client_id)
        client = getattr(client, "name", client)  # Fallback to client id
        self.log.debug(
            "Chat: [%s@%s] %s > %s",
            Action(action).name,
            DestType(type).name,
            client,
            message,
        )

    def on_server_console(self, origin: str, message: str):
        self.log.debug("Console: [%s] %s", origin, message)

    def on_server_cmd_names(self, commands: Dict[int, str]):
        self.log.debug("Received command names")
        self.commands.update(commands)

    def on_server_cmd_logging(
        self,
        client_id: int,
        company_id: int,
        command_id: int,
        param1: int,
        param2: int,
        tile: int,
        text: str,
        frame: int,
    ):
        client = self.clients.get(client_id, client_id)
        client = getattr(client, "name", client)  # Fallback to client id
        company = self.companies.get(company_id, company_id)
        company = getattr(company, "name", company)  # Fallback to company id
        command = self.commands.get(command_id, command_id)
        self.log.debug(
            "Command: [%s/%s] %s > 0x%x 0x%x Tile 0x%x (%s) on frame %d",
            client,
            company,
            command,
            param1,
            param2,
            tile,
            text,
            frame,
        )


if __name__ == "__main__":
    logging.debug("Better get your earmuffs, this might get loud...")
    args = parser.parse_args()
    selector = DefaultSelector()
    client = Client(password=args.password,
                    secret_key=args.secret_key,
                    use_insecure_join=args.use_insecure_join)
    client.connect((args.host, args.port))
    client.setblocking(False)
    client.register_to_selector(selector)

    while len(selector.get_map()):
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
