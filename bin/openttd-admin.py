#!/usr/bin/env python
#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#
import errno
import os
import shlex
import sys
import textwrap
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta

try:
    import urwid
except ImportError as e:
    print >> sys.stderr, "Failed to import urwid: %s" % e
    print >> sys.stderr, "Please check if you have the urwid library installed."
    sys.exit(1)

from libottdadmin2.client import *
from libottdadmin2.enums import *
from libottdadmin2.constants import *

from optparse import OptionParser

usage = "usage: %prog [options]"

parser = OptionParser(usage = usage)
parser.add_option("-H", "--host", dest="host", metavar="HOST",
                  help="connect to HOST", )
parser.add_option("-P", "--port", dest="port", type="int", default=3977, 
                  help="use PORT as port (default: 3977)", metavar="PORT")
parser.add_option("-p", "--password", dest="password", default=None,
                  help="use PASS as password", metavar="PASS")

class ExtendedEdit (urwid.Edit):
    hide_edit_text = False

    def set_hide (self, s):
        if type (s) != bool:
            raise TypeError("Wrong type for s, bool required")
        self.hide_edit_text = s

    def get_text (self):
        text = urwid.Edit.get_text(self)
        if self.hide_edit_text:
            text[0] = len(text[0])*"*"
        return text

class ExtendedListBox(urwid.ListBox):

    __metaclass__ = urwid.MetaSignals
    signals = ["set_auto_scroll"]

    @property
    def auto_scroll(self):
        return self._auto_scroll

    @auto_scroll.setter
    def auto_scroll(self, value):
        if type(value) != bool:
            return
        self._auto_scroll = value
        urwid.emit_signal(self, "set_auto_scroll", value)

    def __init__(self, body):
        urwid.ListBox.__init__(self, body)
        self.auto_scroll = True

    def switch_body(self, body):
        if self.body:
            urwid.disconnect_signal(body, "modified", self._invalidate)

        self.body = body
        self._invalidate()

        urwid.connect_signal(body, "modified", self._invalidate)

    def keypress(self, size, key):
        urwid.ListBox.keypress(self, size, key)

        if key in ("page up", "page down"):
            self.set_focus_valign("bottom")
            #logging.debug("focus = %d, len = %d" % (self.get_focus()[1], len(self.body)))
            if self.get_focus()[1] == len(self.body)-1:
                self.auto_scroll = True
            else:
                self.auto_scroll = False
            #logging.debug("auto_scroll = %s" % (self.auto_scroll))

    def scroll_to_bottom(self):
        #logging.debug("current_focus = %s, len(self.body) = %d" % (self.get_focus()[1], len(self.body)))
        if self.auto_scroll:
            # at bottom -> scroll down
            self.set_focus(len(self.body)-1)
            self.set_focus_valign("bottom")


def except_hook(extype, exobj, extb, manual=False):
    if not manual:
        try:
            main_window.quit(exit=False)
        except NameError:
            pass
        message = "An error occured:\n%(divider)s\n%(traceback)s\n"\
            "%(exception)s\n%(divider)s" % {
                "divider": 20*"-",
                "traceback": "".join(traceback.format_tb(extb)),
                "exception": extype.__name__+": "+str(exobj)
            }
        print >> sys.stderr, message

class ExtendedAdminConnection(AdminClient):
    update_types = [
        (UpdateType.CLIENT_INFO, UpdateFrequency.AUTOMATIC),
        (UpdateType.COMPANY_INFO, UpdateFrequency.AUTOMATIC),
        (UpdateType.CHAT, UpdateFrequency.AUTOMATIC),
        (UpdateType.CONSOLE, UpdateFrequency.AUTOMATIC),
        (UpdateType.DATE, UpdateFrequency.DAILY),
    ]
    def __init_events__(self):
        super(ExtendedAdminConnection, self).__init_events__()
        self.datechanged    = Event()

        self.clientjoin     = Event()
        self.clientinfo     = Event()
        self.clientupdate   = Event()
        self.clientquit     = Event()

        self.companynew     = Event()
        self.companyinfo    = Event()
        self.companyupdate  = Event()
        self.companyremove  = Event()

        self.chat           = Event()
        self.rcon           = Event()
        self.console        = Event()
        self.pong           = Event()

    def __init_handlers__(self):
        super(ExtendedAdminConnection, self).__init_handlers__()
        self._packet_handlers[ServerDate.packetID]          = self.on_serverdate

        self._packet_handlers[ServerClientJoin.packetID]    = self.on_clientjoin
        self._packet_handlers[ServerClientInfo.packetID]    = self.on_clientinfo
        self._packet_handlers[ServerClientUpdate.packetID]  = self.on_clientupdate
        self._packet_handlers[ServerClientQuit.packetID]    = self.on_clientquit
        self._packet_handlers[ServerClientError.packetID]   = self.on_clienterror

        self._packet_handlers[ServerCompanyNew.packetID]    = self.on_companynew
        self._packet_handlers[ServerCompanyInfo.packetID]   = self.on_companyinfo
        self._packet_handlers[ServerCompanyUpdate.packetID] = self.on_companyupdate
        self._packet_handlers[ServerCompanyRemove.packetID] = self.on_companyremove

        self._packet_handlers[ServerChat.packetID]          = self.on_chat
        self._packet_handlers[ServerRcon.packetID]          = self.on_rcon
        self._packet_handlers[ServerConsole.packetID]       = self.on_console
        self._packet_handlers[ServerPong.packetID]          = self.on_pong

    def __init__(self, *args, **kwargs):
        super(ExtendedAdminConnection, self).__init__(*args, **kwargs)
        self.clients = {}
        self.pending_clients = []
        self.pending_companies = []
        self.companies = {
            255: {
                'companyID': 255,
                'name': 'spectators',
                'manager': 'S Tator',
                'colour': 0,
                'passworded': False, 
                'startYear': 1,
                'isAI': False,
            }
        }
        self.pings = {}
        self.date = datetime.min

    def on_connect(self):
        super(ExtendedAdminConnection, self).on_connect()
        for updType, updFreq in self.update_types:
            self.send_packet(AdminUpdateFrequency, updateType = updType, updateFreq = updFreq)

    def on_map_info_received(self, data):
        super(ExtendedAdminConnection, self).on_map_info_received(data)
        self.clients = {}
        self.pending_clients = []
        self.pending_companies = []
        self.send_packet(AdminPoll, pollType = UpdateType.CLIENT_INFO,  extra = 0xFFFFFFFF)
        self.companies = {
            255: {
                'companyID': 255,
                'name': 'spectators',
                'manager': 'S Tator',
                'colour': 0,
                'passworded': False, 
                'startYear': data['startyear'].year,
                'isAI': False,
            }
        }
        self.send_packet(AdminPoll, pollType = UpdateType.COMPANY_INFO, extra = 0xFFFFFFFF)
        self.date = datetime.min
        self.send_packet(AdminPoll, pollType = UpdateType.DATE,         extra = 0xFFFFFFFF)

    def on_serverdate(self, data):
        self.date = data.get('date', datetime.min)
        self.datechanged(self.date)

    def on_clientjoin(self, data):
        self.pending_clients.append(data['clientID'])
        self.clientjoin(data, False)
        self.send_packet(AdminPoll, pollType = UpdateType.CLIENT_INFO, extra = data['clientID'])

    def on_clientinfo(self, data):
        self.clients[data.get('clientID', -1)] = data
        cid = data.get('clientID')
        if cid == ClientID.SERVER:
            self.clients[ClientID.SERVER].update({
                'name': self.map_info['name'],
                'hostname': '%s:%s' % (self.host, self.port),
                'joindate': self.map_info['startyear'],
                'play_as': 255,
                'language': 0,
                })
        if cid in self.pending_clients:
            self.pending_clients.remove(cid)
            self.clientjoin(data, True)
        self.clientinfo(data)

    def on_clientupdate(self, data):
        cid = data.get('clientID')

        old = dict(self.clients.get(cid, {}))
        self.clients.setdefault(cid, {}).update(data)
        newdata = self.clients[cid]
        self.clientupdate(old, newdata)

    def on_clientquit(self, data):
        old = self.clients.get(data['clientID'], {}) 
        self.clientquit(data['clientID'], old, False)
        if data['clientID'] in self.clients:
            del self.clients[data['clientID']]

    def on_clienterror(self, data):
        old = self.clients.get(data['clientID'], {}) 
        self.clientquit(data['clientID'], old, data['errorcode'])
        if data['clientID'] in self.clients:
            del self.clients[data['clientID']]        

    def on_companynew(self, data):
        self.companynew(data, False)
        self.send_packet(AdminPoll, pollType = UpdateType.COMPANY_INFO, extra = data['companyID'])

    def on_companyinfo(self, data):
        cid = data['companyID']
        self.companies[cid] = data
        self.companyinfo(data)
        if cid in self.pending_companies:
            self.pending_companies.remove(cid)
            self.companynew(data, True)

    def on_companyupdate(self, data):
        old = dict(self.companies.get(data['companyID'], {}))
        self.companies.setdefault(data['companyID'], {}).update(data)
        self.companyupdate(old, self.companies[data['companyID']])

    def on_companyremove(self, data):
        if data['companyID'] in self.companies:
            self.companyremove(self.companies[data['companyID']], data['reason'])
            del self.companies[data['companyID']]

    def on_chat(self, data):
        self.chat(data['action'], data['destType'], data['clientID'], data['message'], data['data'])

    def on_rcon(self, data):
        self.rcon(data['result'], data['colour'])

    def on_console(self, data):
        self.console(data['origin'], data['message'])

    def on_pong(self, data):
        if data['payload'] in self.pings:
            start = self.pings[data['payload']]
            end = datetime.now()
            del self.pings[data['payload']]
            self.pong(start, end, end - start)

    def ping(self):
        index = len(self.pings.keys()) + 1
        self.pings[index] = datetime.now()
        self.send_packet(AdminPing, payload = index)


class OpenTTDAdmin(object):
    running = True
    def __init__(self, options, args):
        self.options = options
        self.args = args

        self.connection = None

        self.commands = {}
        self.commands['connect'] = self.cmd_connect
        self.commands['disconnect'] = self.cmd_disconnect
        self.commands['set'] = self.cmd_set
        self.commands['say'] = self.cmd_say
        self.commands['msg'] = self.cmd_msg
        self.commands['cmsg'] = self.cmd_cmsg
        self.commands['rcon'] = self.cmd_rcon
        self.commands['clients'] = self.cmd_clients
        self.commands['companies'] = self.cmd_companies
        self.commands['help'] = self.cmd_help

        self.commands['ping'] = self.cmd_ping

    palette = [
        ('divider', 'black', 'dark cyan', 'standout'),
        ('divider-hilight', 'dark magenta', 'dark cyan', 'standout'),
        ('text','light gray', 'default'),
        ('error', 'light red', 'default'),
        ('bold_text', 'light gray', 'default', 'bold'),
        ("body", "text"),
        ("footer", "text"),
        ("header", "text"),
    ]

    def _init_widgets(self):
        self.generic_output_walker = urwid.SimpleFocusListWalker([])
        self.body       = ExtendedListBox(self.generic_output_walker)
        self.divider    = urwid.Text("")
        self.footer     = ExtendedEdit(">>> ")

        #urwid.connect_signal(self.body, "set_auto_scroll", self.handle_body_auto_scroll)

        self.footer     = urwid.AttrWrap(self.footer, "footer")
        self.body       = urwid.AttrWrap(self.body, "body")
        self.divider    = urwid.AttrWrap(self.divider, "divider")

        self.footer.set_wrap_mode("space")

        self.context    = urwid.Frame(self.body, footer = self.divider)
        self.context    = urwid.Frame(self.context, footer = self.footer)

        self.context.set_focus("footer")

    def _init_ui(self):
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)

        self._init_widgets()
        self.update_divider()

    def update_divider(self, *args):
        markup = []
        if self.connection and self.connection.is_connected:
            markup.append("Connected to: ")
            markup.append(("divider-hilight", "%s:%d" % (self.connection.host, self.connection.port)))
            markup.append(" ")
            if 'version' in self.connection.map_info:
                markup.append("(")
                markup.append(("divider-hilight", self.connection.map_info['version']))
                markup.append(") ")
            if self.connection.date:
                markup.append("Date: ")
                markup.append("%(day)d/%(month)d/%(year)d" % {
                    'day': self.connection.date.day,
                    'month': self.connection.date.month,
                    'year': self.connection.date.year,
                    })
            if 'dedicated' in self.connection.map_info:
                markup.append(", ")
                amount = (len(self.connection.clients) - (1 if self.connection.map_info['dedicated'] else 0))
                markup.append(("divider-hilight", str(amount)))
                markup.append(" player%s" % ("s" if amount != 1 else ""))
        else:
            markup.append("Not connected")
        if not markup:
            self.divider.set_text("")
        else:
            self.divider.set_text(markup)

    def check_settings(self, verbose = True):
        if self.options.password is None:
            if verbose:
                self.append_error("You have no password specified, run with --password=<password> or use 'set password <password>'.")
            return False
        if self.options.host is None:
            if verbose:
                self.append_error("You have no host specified, run with --host=<host> or use 'set host <host>'.")
            return False
        if self.options.port is None:
            if verbose:
                self.append_error("You have no port specified, run with --port=<port> or use 'set port <port>'.")
            return False
        return True

    def poll(self, *args):
        if self.connection:
            try:
                self.connection.poll()
            except IOError as e:
                if e.errno == errno.EINTR:
                    pass
                else:
                    raise
        self.main_loop.set_alarm_in(0.01, self.poll)

    def _attach_events(self):
        self.connection.connected       += self.update_divider
        self.connection.disconnected    += self.update_divider
        self.connection.datechanged     += self.update_divider
        self.connection.map_info_received += self.map_info_received

        self.connection.pong            += self.on_pong
        self.connection.chat            += self.on_chat
        self.connection.rcon            += self.on_rcon
        #self.connection.console         += self.on_console

        self.connection.clientjoin      += self.on_clientjoin
        self.connection.clientquit      += self.on_clientquit
        self.connection.clientupdate    += self.on_clientupdate

    def _detach_events(self):
        self.connection.connected       -= self.update_divider
        self.connection.disconnected    -= self.update_divider
        self.connection.datechanged     -= self.update_divider
        self.connection.map_info_received -= self.map_info_received

        self.connection.pong            -= self.on_pong
        self.connection.chat            -= self.on_chat
        self.connection.rcon            -= self.on_rcon
        #self.connection.console         -= self.on_console

        self.connection.clientjoin      -= self.on_clientjoin
        self.connection.clientquit      -= self.on_clientquit
        self.connection.clientupdate    -= self.on_clientupdate


    def map_info_received(self, data):
        self.update_divider()

    def cmd_ping(self, args):
        if self.connection is None or self.connection.is_connected == False:
            self.append_error("We are not connected.")
            return
        self.connection.ping()

    def on_pong(self, start, end, taken):
        self.append("PONG] response took: %s" % str(taken))

    def cmd_help(self, args):
        self.append("Available commands:")
        commands = ' | '.join(self.commands.keys())
        for line in textwrap.wrap(commands):
            line = line.strip('|').strip()
            self.append(line)

    def cmd_clients(self, args):
        if self.connection is None or self.connection.is_connected == False:
            self.append_error("We are not connected.")
            return
        self.append("%s Clients %s" % ('-' * 16, '-' * 16))
        format = "%(clientID)3s | %(name)16s | %(hostname)16s"
        for id, client in sorted(self.connection.clients.items()):
            self.append(format % client)

    def cmd_companies(self, args):
        if self.connection is None or self.connection.is_connected == False:
            self.append_error("We are not connected.")
            return

        players = defaultdict(list)
        for id, client in self.connection.clients.items():
            players[client['play_as']].append(client)

        self.append("%s Companies %s" % ('-' * 15, '-' * 15))
        format  = "%(companyID)3s | %(name)16s | %(manager)16s"
        pformat = " => | %(name)s [#%(clientID)s]"
        for id, company in sorted(self.connection.companies.items()):
            self.append(format % company)
            for client in players[id]:
                self.append(pformat % client)

    def cmd_set(self, args):
        if len(args) != 2:
            self.append_error("set requires 2 arguments: set <name> <value>")
            return
        key = args[0].lower()
        val = args[1]
        if key not in ('host', 'port', 'password'):
            self.append_error("Can only set host, port or password")
            return
        if key == "host":
            self.options.host = val
            self.append("Host set to %s" % val)
        elif key == "port":
            try:
                val = int(val)
                self.options.port = val
                self.append("Port set to %d" % val)
            except ValueError:
                self.append_error("%s is not a valid port number" % val)
                return
        elif key == "password":
            self.options.password = val
            self.append("Password set.")

    def on_clientjoin(self, data, is_join_full):
        if not is_join_full:
            return
        self.append_chat(origin = data['name'], type="JOIN", message="Joined the game")

    def on_clientquit(self, id, data, error):
        if error is not False:
            return
        if not data.keys():
            self.append_chat(origin = "ClientID:#%s" % id, type="QUIT", message="Disconnected")
        else:
            self.append_chat(origin = data['name'], type="QUIT", message="Disconnected")

    def on_clientupdate(self, old, new):
        if old['name'] != new['name']:
            self.append_chat(origin = old['name'], type="UPDATE", message="Renamed to '%s'" % new['name'])
        if old['play_as'] != new['play_as']:
            oldc = self.connection.companies.get(old['play_as'])
            newc = self.connection.companies.get(new['play_as'])
            if not oldc or not newc:
                return
            self.append_chat(origin = old['name'], type="UPDATE", message="Left team '%s' to join '%s'" % (oldc['name'], newc['name']))

    def on_chat(self, action, destType, clientID, message, data):
        client = self.connection.clients.get(clientID, None)
        name = str(clientID)
        if client:
            name = client['name']
        if action == Action.CHAT:
            self.append_chat(origin = name, type="CHAT", message=message)
        elif action == Action.CHAT_COMPANY:
            self.append_chat(origin = name, type="TEAM", message=message)
        elif action == Action.CHAT_CLIENT:
            self.append_chat(origin = name, type="CLIENT", message=message)

    def on_rcon(self, result, colour):
        self.append_chat(origin = None, type="RCON", message=result)

    def on_console(self, origin, message):
        self.append_chat(origin = origin, type="CONSOLE", message=message)

    def cmd_say(self, original, args):
        if self.connection is None or self.connection.is_connected == False:
            self.append_error("We are not connected.")
            return

        for part in textwrap.wrap(original, NETWORK_CHAT_LENGTH):
            self.connection.send_packet(AdminChat, action = Action.CHAT, destType = DestType.BROADCAST, clientID = 0, message = part)
        self.append_chat(origin="to: ALL", type="CHAT", message = original)

    def cmd_msg(self, original, args):
        self.send_directed('msg', Action.CHAT_CLIENT, DestType.CLIENT, original, self.connection.clients)

    def cmd_cmsg(self, original, args):
        self.send_directed('msg', Action.CHAT_COMPANY, DestType.TEAM, original, self.connection.companies)

    def send_directed(self, cmdname, chattype, cmdtype, original, pool):
        if self.connection is None or self.connection.is_connected == False:
            self.append_error("We are not connected.")
            return
        parts = original.split(' ', 1)
        if len(parts) < 2:
            self.append_error("Format: %s <person> <text>" % cmdname)
            return
        to = None
        for index, item in pool.items():
            if item['name'] == parts[0]:
                to = index
                break
        if to is None:
            try:
                to = int(parts[0])
                if to not in pool:
                    to = None
            except:
                pass
        if to is None:
            self.append_error("Cannot find a target by the name (or id) of '%s'" % parts[0])
            return
        for part in textwrap.wrap(parts[1], NETWORK_CHAT_LENGTH - 1):
            self.connection.send_packet(AdminChat, action = chattype, destType = cmdtype, clientID = to, message = part)
        self.append_chat(origin="<to: %s" % pool[to]['name'], type=DestType.get_name(cmdtype), message = parts[1])

    def cmd_rcon(self, original, args):
        if len(original) >= NETWORK_RCONCOMMAND_LENGTH:
            self.append_error("RCON Command too long (%d/%d)" % (len(original), NETWORK_RCONCOMMAND_LENGTH))
            return
        self.connection.send_packet(AdminRcon, command = original)
        self.append_chat(origin=None, type="RCON", message=original)

    def cmd_connect(self, args):
        self.connect()

    def connect(self, verbose = True):
        if self.connection is not None:
            if self.connection.is_connected:
                if verbose:
                    self.append_error("Cannot connect, we're already connected.")
                return
            self.connection = None
        if not self.check_settings(verbose):
            return
        self.connection = ExtendedAdminConnection()
        self.connection.configure(
            host = self.options.host,
            port = self.options.port,
            password = self.options.password,
            timeout = 0.1)
        self._attach_events()
        self.append("Connecting to: %(host)s:%(port)d" % {'host': self.options.host, 'port': self.options.port})
        self.connection.connect()

    def cmd_disconnect(self, *args):
        if self.connection and self.connection.is_connected:
            self.append("Disconnecting")
            self.connection.disconnect()
        else:
            self.append_error("We are not connected")

    def main(self):
        self.running = True
        self._init_ui()

        self.ui.run_wrapper(self.run)

    def draw(self):
        self.main_loop.draw_screen()

    def run(self):       

        def redraw(*args):
            self.draw()
            invalidate.locked = False

        invalidate_old = urwid.canvas.CanvasCache.invalidate
        def invalidate(cls, *args, **kwargs):
            invalidate_old(*args, **kwargs)
            if not invalidate.locked:
                invalidate.locked = True
                self.main_loop.set_alarm_in(0, redraw)
        invalidate.locked = False
        urwid.canvas.CanvasCache.invalidate = classmethod(invalidate)

        def do_input(key):
            if not self.running:
                raise urwid.ExitMainLoop()
            self.keypress(self.ui.get_cols_rows(), key)

        self.main_loop = urwid.MainLoop(self.context, screen=self.ui, handle_mouse=False, unhandled_input=do_input)
        self.poll()

        self.connect(False)

        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            self.quit()

    def quit(self, exit=True):
        self.running = False
        if exit:
            sys.exit(0)

    def handle_command(self):
        data = self.footer.get_edit_text()
        self.footer.set_edit_text(" "*len(data))
        self.footer.set_edit_text("")
        if len(data) < 1:
            return
        parts = data.split(' ', 1)
        if len(parts) < 1:
            return
        command = parts[0]
        args_orig = ''
        if len(parts) > 1:
            args_orig = parts[1]
        args = shlex.split(args_orig)

        if command.lower() in self.commands:
            try:
                self.commands[command.lower()](original = args_orig, args = args)
            except Exception as e:
                try:
                    self.commands[command.lower()](args)
                except Exception as e2:
                    self.append_error(str(e))
                    self.append_error(str(e2))

    def append_chat(self, origin, type, message):
        cols = []
        if type is not None:
            cols.append( ('pack', urwid.Text("%8s]" % type)))
        if origin is not None:
            cols.append( ('pack', urwid.Text("%10s>" % origin)))
        cols.append( ('weight', 100, urwid.Text(message)) )
        self.append_raw(urwid.Columns(cols, dividechars=1))

    def append(self, text):
        self.append_raw(urwid.Text(text))

    def append_error(self, text):
        self.append_raw(urwid.AttrWrap(urwid.Text(text), "error"))

    def append_raw(self, item):
        line = urwid.Columns([
                ('pack', urwid.Text("%8s ]" % datetime.now().strftime('%H:%M:%S'))),
                ('weight', 100, item)
            ], dividechars = 1)
        self.generic_output_walker.append(line)
        self.body.scroll_to_bottom()

    def keypress(self, size, key):
        if key in ("page up", "page down"):
            self.body.keypress(size, key)
        elif key == "enter":
            self.handle_command()
        elif key == "up":
            pass
        elif key == "down":
            pass
        else:
            self.context.keypress(size, key)

if __name__ == "__main__":
    global main_window
    options, args = parser.parse_args()

    main_window = OpenTTDAdmin(options, args)

    sys.excepthook = except_hook

    main_window.main()
