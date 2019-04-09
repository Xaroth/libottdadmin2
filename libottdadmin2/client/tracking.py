from datetime import datetime
from typing import Tuple, Any

from libottdadmin2.enums import UpdateType, UpdateFrequency, PollExtra, Colour
from libottdadmin2.packets import AdminPoll, Packet
from libottdadmin2.packets import AdminUpdateFrequency
from libottdadmin2.util import SimpleDataclass
from packets import ServerCompanyInfo


class TrackingMixIn:
    update_types = {
        UpdateType.CLIENT_INFO: UpdateFrequency.AUTOMATIC | UpdateFrequency.POLL,
        UpdateType.COMPANY_INFO: UpdateFrequency.AUTOMATIC | UpdateFrequency.POLL,
        UpdateType.COMPANY_ECONOMY: UpdateFrequency.MONTHLY | UpdateFrequency.POLL,
        UpdateType.COMPANY_STATS: UpdateFrequency.MONTHLY | UpdateFrequency.POLL,
        UpdateType.CHAT: UpdateFrequency.AUTOMATIC,
        UpdateType.CONSOLE: UpdateFrequency.AUTOMATIC,
        UpdateType.DATE: UpdateFrequency.DAILY | UpdateFrequency.POLL,
        UpdateType.NAMES: UpdateFrequency.POLL,
    }

    current_date = datetime.min
    clients = None
    companies = None

    def on_server_protocol_raw(self, packet, data):
        self.protocol_info = data

    def _reset(self):
        startyear = datetime.min.year
        if self.server_info and self.server_info.startdate:
            startyear = self.server_info.startdate.year
        self.current_date = datetime.min
        self.clients = {}
        self.commands = {}
        self.companies = {
            255: ServerCompanyInfo.data(company_id=255, name='Spectators', manager='Spec Tator', colour=0,
                                        passworded=False, startyear=startyear,
                                        is_ai=False, bankrupcy_counter=0, shareholders=[255, 255, 255, 255])
        }
        self.economy = {}
        self.company_stats = {}

    def on_server_welcome_raw(self, packet, data):
        self.server_info = data
        self._reset()

        for _type, freq in self.update_types.items():
            self.log.debug("Processing update type: %s (%s)", _type.name, freq)
            if freq ^ UpdateFrequency.POLL:
                self.log.debug("Requesting updates")
                self.send_packet(AdminUpdateFrequency.create(type=_type, freq=freq & ~UpdateFrequency.POLL))
            if freq & UpdateFrequency.POLL:
                self.log.debug("Polling current values")
                self.send_packet(AdminPoll.create(type=_type, extra=PollExtra.ALL))

    # Tracking packets

    def on_server_new_game(self):
        self._reset()

    def on_server_date(self, date):
        self.current_date = date
        if date.day == 2:
            self.log.debug("Company details")
            for company_id, economy in self.economy.items():
                if company_id not in self.companies or company_id not in self.company_stats:
                    continue
                info = self.companies[company_id]
                stats = self.company_stats[company_id]
                self.log.debug("%d: %s (%s)", company_id, info.name, info.manager)
                self.log.debug("%d: %r", company_id, economy)
                self.log.debug("%d: Vehicles: %r, Stations: %r", company_id, stats.vehicles, stats.stations)

    def on_server_client_info_raw(self, packet, data):
        self.clients[data.client_id] = data

    def on_server_client_update_raw(self, packet, data):
        if data.client_id in self.clients:
            self.clients[data.client_id] = self.clients[data.client_id]._replace(**data._asdict())

    def on_server_client_quit(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]

    def on_sever_client_error(self, client_id, errorcode):
        self.on_server_client_quit(client_id=client_id)

    def on_server_cmd_names(self, commands):
        self.commands.update(commands)

    def on_server_company_new(self, company_id):
        print("company_id", company_id)

    def on_server_company_info_raw(self, packet, data):
        self.companies[data.company_id] = data

    def on_server_company_update_raw(self, packet, data):
        if data.company_id in self.companies:
            self.companies[data.company_id] = self.companies[data.company_id]._replace(**data._asdict())

    def on_server_company_remove(self, company_id, reason):
        if company_id in self.companies:
            del self.companies[company_id]
        if company_id in self.economy:
            del self.economy[company_id]
        if company_id in self.company_stats:
            del self.company_stats[company_id]

    def on_server_company_economy_raw(self, packet, data):
        self.economy[data.company_id] = data

    def on_server_company_stats_raw(self, packet, data):
        self.company_stats[data.company_id] = data
