#!/usr/bin/env python
#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#
from __future__ import print_function

import sys
import os
import warnings

main_window = None

try:
    import urwid
except ImportError as ex:
    print("Failed to import urwid: %s" % ex, file=sys.stderr)
    print("Please check if you have the urwid library installed.", file=sys.stderr)
    sys.exit(1)

try:
    import libottdadmin2
except ImportError as ex:
    DNAME = os.path.abspath(os.path.dirname(__file__))
    ROOTDIR = os.path.dirname(DNAME)
    if os.path.exists(os.path.join(ROOTDIR, 'libottdadmin2')):
        warnings.warn("libottdadmin2 is not installed; "
            "attempting to work around by path insertion", RuntimeWarning)
        sys.path.append(ROOTDIR)
        try:
            import libottdadmin2
        except ImportError:
            print("Failed to import libottdadmin2: %s" % ex, file=sys.stderr)
            sys.exit(1)
    else:
        print("Failed to import libottdadmin2: %s" % ex, file=sys.stderr)
        sys.exit(1)


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
        print(message, file=sys.stderr)


import errno
from libottdadmin2.trackingclient import *
from libottdadmin2.enums import *
from libottdadmin2.constants import *
from libottdadmin2.util import int_type
import shlex
import textwrap
import traceback

from optparse import OptionParser

usage = "usage: %prog [options]"

parser = OptionParser(usage = usage)
parser.add_option("-H", "--host", dest="host", metavar="HOST",
                  help="connect to HOST", )
parser.add_option("-P", "--port", dest="port", type="int", default=3977, 
                  help="use PORT as port (default: 3977)", metavar="PORT")
parser.add_option("-p", "--password", dest="password", default=None,
                  help="use PASS as password", metavar="PASS")
parser.add_option("-i", "--interval", dest="timeout", default=0.1, type="float",
                  help="use X as polling interval (Advanced use only)", metavar="X")


def swallow_args(func):
    def _inner(self, *args):
        return func(self)
    return _inner


def command(*items):
    def __inner(func):
        func.commands = items
        return func
    return __inner


class MaskableEdit (urwid.Edit):
    _hide_text = False
    _text_mask = "*"

    @property
    def text_mask(self):
        return self._text_mask

    @text_mask.setter
    def text_mask(self, value):
        self._text_mask = value
        self._invalidate()

    @property
    def hide_text(self):
        return self._hide_text

    @hide_text.setter
    def hide_text(self, value):
        if type(value) != bool:
            raise TypeError("Wrong type, bool required")
        self._hide_text = value
        self._invalidate()

    def get_text (self):
        text = urwid.Edit.get_text(self)
        if self._hide_text:
            text[0] = len(text[0])*"*"
        return text


class ScrollingListBox(urwid.ListBox):
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
        self._invalidate()

    def _invalidate(self, *args, **kwargs):
        focus_widget, focus_pos = self.body.get_focus()
        if focus_widget:
            self.scroll_to_bottom()
        super(ScrollingListBox, self)._invalidate(*args, **kwargs)

    def __init__(self, body):
        urwid.ListBox.__init__(self, body)
        self._auto_scroll = True

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
            if self.get_focus()[1] == len(self.body)-1:
                self.auto_scroll = True
            else:
                self.auto_scroll = False

    def scroll_to_bottom(self):
        if self.auto_scroll:
            # at bottom -> scroll down
            self.set_focus(len(self.body)-1)
            self.set_focus_valign("bottom")


class ConnectionState(EnumHelper):
    DISCONNECTED = 0x00
    CONNECTING = 0x01
    AUTHENTICATING = 0x02
    CONNECTED = 0x03
    DISCONNECTING = 0x04


class OpenTTDAdmin(object):
    _running = True
    _state = ConnectionState.DISCONNECTED

    _connection = None
    _poll_interval = 0.1

    _output_list = None
    _body = None
    _divider = None
    _current_markup = None
    _footer = None
    _context = None

    _history = None
    _hist_index = -1
    _hist_last = None

    command_handlers = {}
    debug = False

    _ui = None
    _main_loop = None

    _palette = [
        ('divider', 'black', 'dark cyan', 'standout'),
        ('divider-hilight', 'dark magenta', 'dark cyan', 'standout'),
        ('text','light gray', 'default'),
        ('error', 'light red', 'default'),
        ('notice', 'light green', 'default'),
        ('bold_text', 'light gray', 'default', 'bold'),
        ("body", "text"),
        ("footer", "text"),
        ("header", "text"),
    ]

    ERROR_MESSAGES = {
        "NOT_CONNECTED":    "We are not connected",
    }

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        invalidate = self._state != value
        self._state = value
        if invalidate:
            self.invalidate()

    @property
    def running(self):
        return self._running

    @property
    def connection(self):
        return self._connection

    @swallow_args
    def poll(self):
        self._main_loop.set_alarm_in(self._poll_interval, self.poll)
        if not self.running:
            return
        try:
            self.connection.poll()
        except IOError as e:
            if e.errno == errno.EINTR:
                pass
            else:
                raise
        if not self.connection.is_connected:
            self.state = ConnectionState.DISCONNECTED

    @swallow_args
    def _connected(self):
        self.state = ConnectionState.AUTHENTICATING
        self.add_notice("Connected, Authenticating")

    def _protocol(self, protocol):
        self.state = ConnectionState.CONNECTED
        self.add_notice("Authentication successful, server is running network version %d" % protocol.version)

    @swallow_args
    def _disconnected(self):
        if self.state != ConnectionState.DISCONNECTED:
            self.state = ConnectionState.DISCONNECTED
            self.add_notice("Disconnected from server")

    def _pong(self, start, end, taken):
        self.add_notice("PONG] response took: %s" % str(taken))

    def _rcondata(self, result, colour):
        return self.add_chat(origin = "RCON", message = result)

    def _chat(self, client, action, destType, clientID, message, data):
        name = str(clientID)
        company = None
        if client != clientID:
            company = self.connection.companies.get(client.play_as, None)
            name = client.name
        if company:
            company = company.name
        if action == Action.CHAT:
            self.add_chat(origin=name, message=message)
        elif action == Action.CHAT_COMPANY:
            self.add_chat(origin=name, target=company or ' ', message=message)
        elif action == Action.CHAT_CLIENT:
            if data in self.connection.clients:
                target = self.connection.clients[data].name 
            else:
                target = None
            self.add_chat(origin=name, target=target or ' ', message=message)

    def _clientjoin(self, client):
        if isinstance(client, int_type):
            return
        self.add_chat(origin=client.name, is_action=True, message="joined the game")

    def _clientupdate(self, old, client, changed):
        if 'play_as' in changed:
            company = self.connection.companies.get(client.play_as)
            self.add_debug("Client joined company ID: %d" % client.play_as)
            if company:
                self.add_chat(origin=client.name, is_action=True, message="joined company '%s'" % company.name)
            else:
                self.add_chat(origin=client.name, is_action=True, message="started a new company (#%d)" % client.play_as)
        if 'name' in changed:
            self.add_chat(origin=old.name, is_action=True, message="is now known as %s" % client.name)

    def _clientquit(self, client, errorcode):
        if isinstance(client, int_type):
            return
        self.add_chat(origin=client.name, is_action=True, message="left the game")

    def _init_widgets_(self):
        self._output_list = urwid.SimpleFocusListWalker([])
        self._body = urwid.AttrWrap(ScrollingListBox(self._output_list), "body")
        self._divider = urwid.AttrWrap(urwid.Text(""), "divider")
        self._footer = urwid.AttrWrap(MaskableEdit(">>> "), "footer")

        self._footer.set_wrap_mode("space")

        self._context = urwid.Frame(
                                    urwid.Frame(
                                        self._body, 
                                        footer = self._divider
                                    ),
                                    footer = self._footer
                                )
        self._context.set_focus("footer")

    def _init_ui_(self):
        self._ui = urwid.raw_display.Screen()
        self._ui.register_palette(self._palette)

    def _init_connection_(self):
        conn = self._connection = TrackingAdminClient()

        conn.events.connected += self._connected
        conn.events.protocol += self._protocol
        conn.events.datechanged += self.invalidate
        conn.events.new_map += self.invalidate
        conn.events.disconnected += self._disconnected
        conn.events.pong += self._pong

        conn.events.chat += self._chat
        conn.events.rcon += self._rcondata

        conn.events.clientjoin += self._clientjoin
        conn.events.clientupdate += self._clientupdate
        conn.events.clientquit += self._clientquit

    def _init_handlers_(self):
        self._history = []
        self.command_handlers = {}
        for func in dir(self):
            if func.startswith('__'):
                continue
            func = getattr(self, func)
            if not hasattr(func, 'commands'):
                continue
            for command in func.commands:
                self.command_handlers[command] = func

    def __init__(self, options, args):
        self.options = options
        self.args = args

        self._init_connection_()

        self._init_ui_()
        self._init_widgets_()
        self._init_handlers_()

    def validate_options(self):
        return {
            'password':     self.options.password is not None,
            'host':         self.options.host is not None,
            'port':         self.options.port is not None,
            'timeout':      self.options.timeout is not None,
        }
        
    @command("connect")
    @swallow_args
    def connect(self):
        if self.connection.is_connected:
            # warn connected
            return
        validated_options = self.validate_options()
        if not all(validated_options.values()):
            if not validated_options['password']:
                self.add_error("Password not set, run with --password=<PASSWORD> or use 'set password <PASSWORD>'")
            elif not validated_options['host']:
                self.add_error("Host not set, run with --host=<HOST> or use 'set host <HOST>'")
            elif not validated_options['port']:
                self.add_error("Port not set, run with --port=<PORT> or use 'set port <PORT>'")
            elif not validated_options['timeout']:
                self.add_error("Interval timeout not set")
            return
        self._connection = self._connection.copy()
        self._connection.configure(
            host=self.options.host,
            port=self.options.port,
            password=self.options.password,
            timeout=self.options.timeout or 0.1,
            )
        self.add_notice("Connecting to '%s:%d'" % (self._connection.host, self._connection.port))
        self.state = ConnectionState.CONNECTING
        if not self._connection.connect():
            self.add_error("Unable to connect.")
            self.add_exception(self._connection._last_error)

    @command("disconnect")
    @swallow_args
    def disconnect(self):
        if self.connection.is_connected:
            self.add_notice("Disconnecting")
            self.state = ConnectionState.DISCONNECTING
            self._connection.disconnect()
        else:
            self.add_error("NOT_CONNECTED")

    @swallow_args
    def invalidate(self):
        markup = ["%8s ] " % datetime.now().strftime("%H:%M:%S")]
        if self.state == ConnectionState.DISCONNECTED:
            markup.append("Disconnected")
        elif self.state == ConnectionState.DISCONNECTING:
            markup.append("Disconnecting...")
        elif self.state == ConnectionState.CONNECTING:
            markup.append("Connecting to: ")
        elif self.state == ConnectionState.CONNECTED:
            markup.append("Connected to: ")
        elif self.state == ConnectionState.AUTHENTICATING:
            markup.append("Authenticating with: ")
        if self.state in (ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.AUTHENTICATING):
            markup.append(("divider-hilight", "%s:%d " % (self.connection.host, self.connection.port)))

        if self.state == ConnectionState.CONNECTED:
            if self.connection.serverinfo.version:
                markup.append("(")
                markup.append(("divider-hilight", self.connection.serverinfo.version))
                markup.append(") ")
            if self.connection.date:
                markup.append("Date: ")
                markup.append(("divider-hilight", "%(day)d/%(month)d/%(year)d " % {
                    'day': self.connection.date.day,
                    'month': self.connection.date.month,
                    'year': self.connection.date.year,
                    }))
            if self.connection.serverinfo.dedicated:
                amt = (len(self.connection.clients) - (1 if self.connection.serverinfo.dedicated else 0))
                companies = len(self.connection.companies) - 1
                markup.append("[")
                markup.append(("divider-hilight", "%d" % amt))
                markup.append(" players, ")
                markup.append(("divider-hilight", "%d" % companies))
                markup.append(" compan%s]" % ("y" if companies == 1 else "ies"))

        if markup != self._current_markup:
            if not markup:
                self._divider.set_text("")
            else:
                self._divider.set_text(markup)
        self._current_markup = markup

    def draw(self):
        self._main_loop.draw_screen()

    def main(self):
        self._running = True
        self._ui.run_wrapper(self.run)

    def run(self):
        def redraw(*args):
            self.draw()
            invalidate.locked = False
        invalidate_old = urwid.canvas.CanvasCache.invalidate

        def invalidate(cls, *args, **kwargs):
            invalidate_old(*args, **kwargs)
            if not invalidate.locked:
                invalidate.locked = True
                self._main_loop.set_alarm_in(0, redraw)
        invalidate.locked = False
        urwid.canvas.CanvasCache.invalidate = classmethod(invalidate)

        def do_input(key):
            if not self.running:
                raise urwid.ExitMainLoop()
            self.keypress(self._ui.get_cols_rows(), key)
        self._main_loop = urwid.MainLoop(self._context, screen=self._ui, handle_mouse=False, unhandled_input=do_input)
        
        self._main_loop.set_alarm_in(0.1, self.poll)
        self._main_loop.set_alarm_in(0.2, self.connect)

        try:
            self._main_loop.run()
        except KeyboardInterrupt:
            self.quit()

    @command("quit")
    @swallow_args
    def _quit(self):
        self.quit(True)

    def quit(self, exit=True):
        self._running = False
        if self.connection.is_connected:
            self.disconnect()
        if exit:
            sys.exit(0)

    def add_debug(self, text):
        if self.debug:
            self.add_line(text)

    def add_line(self, text, display_type="text", display_time=None, align="left"):
        return self.add_raw(urwid.AttrWrap(urwid.Text(text, align=align), display_type), display_time=display_time)

    def add_error(self, text, display_time=None):
        if text in self.ERROR_MESSAGES:
            text = self.ERROR_MESSAGES[text]
        return self.add_line(text, "error", display_time=display_time)

    def add_exception(self, exception, display_time=None):
        return self.add_line(str(exception), "error", display_time=display_time or "error")

    def add_notice(self, text, display_time=None):
        return self.add_line(text, "notice", display_time=display_time)

    def add_table(self, header, values, center_header=False):
        def get_max(x):
            return max([len(str(item[x])) or 1 for item in values] + [len(x),])
        columns = dict([(item, get_max(item)) for item in header])
        total_width = float(sum(columns.values()))
        columns = dict([(item, int((val / total_width) * 100)) for item, val in columns.items()])

        lines = [[('weight', columns[item], urwid.Text(item, align='center' if center_header else 'left')) for item in
                  header]]

        lines.extend([
            [('weight', columns[item], urwid.Text(str(line[item]) or " ")) for item in header]
            for line in values])
        for line in lines:
            self.add_raw(urwid.Columns(line, dividechars=1))

    def add_chat(self, origin, message, target=None, origin_type="text", target_type="notice", is_action=False):
        markup = []
        if is_action:
            markup.append("* ")
        markup.append((origin_type, origin))
        if target:
            markup.append(("bold_text", "@"))
            markup.append((target_type, target))
        if not is_action:
            markup.append(("bold_text", "> "))
        else:
            markup.append(" ")
        markup.append(("text", message))
        if is_action:
            markup.append(" *")
        return self.add_raw(urwid.Text(markup))

    def add_raw(self, item, display_time=None):
        line = urwid.Columns([
                ('pack', urwid.AttrWrap(
                                urwid.Text("%8s ]" % datetime.now().strftime("%H:%M:%S")), 
                                display_time or "text")),
                ('weight', 100, item)
            ], dividechars=1)
        self._output_list.append(line)

    def history_scroll(self, direction=1):
        self.add_debug("history_scroll: %d" % direction)
        if len(self._history) < 1:
            return
        index = self._hist_index + direction
        self.add_debug("index: %d" % index)
        if index < 0:
            if self._hist_index == 0:
                self.set_edit(self._hist_last or "")
                self._hist_last = None
            elif self._hist_index == -1 and index == -2:
                self.set_edit(self._hist_last or "")
                self._hist_last = None
            index = -1
            return
        elif index >= len(self._history):
            index = len(self._history) - 1
        try:
            item = self._history[index]
        except:
            self.add_debug("no item at index, aborting")
            return
        if self._hist_index == -1:
            self.add_debug("setting last item.")
            self._hist_last = self.clear_edit()
        self._hist_index = index
        self.set_edit(item)

    def keypress(self, size, key):
        if key in ("page up", "page down"):
            self._body.keypress(size, key)
        elif key == "enter":
            self.handle_command()
        elif key == "up":
            self.history_scroll()
        elif key == "down":
            self.history_scroll(-1)
        else:
            self._context.keypress(size, key)

    def set_edit(self, text):
        self.clear_edit()
        self._footer.set_edit_text(text)
        self._footer.set_edit_pos(len(text))

    def clear_edit(self):
        data = self._footer.get_edit_text()
        self._footer.set_edit_text(" "*len(data))
        self._footer.set_edit_text("")
        return data

    def handle_command(self):
        line = self.clear_edit()
        ret = self.do_cmd(line)
        if ret != -1:
            self._history.insert(0, line)
            self._hist_index = -1

    def do_cmd(self, line):
        if len(line) < 1:
            return -1  # Don't record this command in the history list
        parts = line.split(' ', 1)
        if len(parts) < 1:
            return -1  # Don't record this command in the history list
        command = parts[0]
        args_orig = ''
        if len(parts) > 1:
            args_orig = parts[1]
        args = shlex.split(args_orig)
        if command in self.command_handlers:
            return self.command_handlers[command](command, args_orig, args)
        else:
            self.add_error("Unknown command: '%s'" % command)

    @command("history")
    @swallow_args
    def _showhistory(self):
        hist = self._history[:]
        hist.reverse()
        for i, line in enumerate(hist):
            self.add_line("%5d : %s" % (i, line))
        return -1 # Don't record this command in the history list

    @command("help", "?")
    @swallow_args
    def _help(self):
        commands = sorted(self.command_handlers.keys())
        self.add_notice("Available commands:")
        self.add_line(", ".join(commands))
        return -1 # Don't record this command in the history list

    @command("set")
    def _set(self, cmd, args_orig, args):
        if len(args) != 2:
            self.add_error("`%(name)s` requires 2 arguments: `%(name)s <name> <value>`" % {'name': cmd})
            return
        key = args[0].lower()
        val = args[1]
        if key not in ('host', 'port', 'password', 'debug'):
            self.add_error("`%(name)s` can only set host, port or password" % {'name': cmd})
            return
        if key == "host":
            self.options.host = val
            self.add_notice("Host set to '%s'" % val)
        elif key == "port":
            try:
                val = int(val)
                if val > 65535 or val <= 0:
                    raise ValueError()
                self.options.port = val
                self.add_notice("Port set to '%d'" % val)
            except ValueError:
                self.add_error("'%s' is not a valid port number (1-65535)" % str(val))
        elif key == "password":
            self.options.password = val
            self.add_notice("Password set")
            return -1 # Don't record this command in the history list
        elif key == "debug":
            if val.lower() in ("true", "1", "on"):
                self.debug = True
                self.add_notice("Debug enabled")
            elif val.lower() in ("false", "0", "off"):
                self.debug  = False
                self.add_notice("Debug disabled")

    @command("clients", "players")
    @swallow_args
    def _clients(self):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        clientlist = [x.to_dict() for x in self.connection.clients.values()]
        headers = [
            "id",
            "name", 
            "hostname", 
            "play_as",
        ]
        self.add_line("Client list", align="center")
        self.add_table(headers, clientlist)

    @command("companies", "teams")
    @swallow_args
    def _companies(self):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        companylist = [x.to_dict() for x in self.connection.companies.values()]
        headers = [
            "id",
            "name",
            "manager",
            "ai",
            "passworded",
            "startyear",
        ]
        self.add_line("Company list", align="center")
        self.add_table(headers, companylist)

    @command("economy")
    @swallow_args
    def _economy(self):
        economylist = [dict(x.economy.to_dict(), **x.to_dict()) for x in self.connection.companies.values()]
        headers = [
            "id",
            "name",
            "money",
            "currentLoan",
            "income",
        ]
        self.add_line("Economy stats", align="center")
        self.add_table(headers, economylist)

    @command("vehicles")
    @swallow_args
    def _vehicles(self):
        stats = [dict(x.vehicles.to_dict(), **x.to_dict()) for x in self.connection.companies.values()]
        headers = [
            "id",
            "name",
            "train",
            "bus",
            "lorry",
            "plane",
            "ship",
        ]
        self.add_line("Vehicle stats", align="center")
        self.add_table(headers, stats)

    @command("stations")
    @swallow_args
    def _stations(self):
        stats = [dict(x.stations.to_dict(), **x.to_dict()) for x in self.connection.companies.values()]
        headers = [
            "id",
            "name",
            "train",
            "bus",
            "lorry",
            "plane",
            "ship",
        ]
        self.add_line("Station stats", align="center")
        self.add_table(headers, stats)

    @command("full_stats")
    @swallow_args
    def _full_stats(self):
        self._clients()
        self._companies()
        self._economy()
        self._vehicles()
        self._stations()

    @command("client", "player")
    def _client(self, cmd, args_orig, args):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        if len(args) < 1:
            return self._clients()
        if args[0].lower() == 'list':
            return self._clients()
        clients = {}
        for arg in args:
            try:
                arg = int(arg)
                if arg not in self.connection.clients:
                    raise ValueError()
                clients[arg] = self.connection.clients[arg]
            except ValueError:
                self.add_debug("'%s' is not an int, or not a valid clientID" % arg)
                matches = [x for _, x in self.connection.clients.items() if arg in x.name]
                if len(matches) < 1:
                    self.add_notice("No client matches: '%s'" % arg)
                    continue
                for item in matches:
                    clients[item.id] = item
        format = "%14s %s"
        for item in clients.values():
            data = item.to_dict()
            company = self.connection.companies.get(item.play_as, None)
            self.add_line("Player info")
            for key in ('id', 'name', 'hostname', 'joindate'):
                self.add_line(format % (key, data[key]))
            if company:
                self.add_line(format % ("company", company.name))

    @command("company", "team")
    def _company(self, cmd, arg_orig, args):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        if len(args) < 1:
            return self._companies()
        if args[0].lower() == 'list':
            return self._companies()
        companies = {}
        for arg in args:
            try:
                arg = int(arg)
                if arg not in self.connection.companies:
                    raise ValueError()
                companies[arg] = self.connection.companies[arg]
            except ValueError:
                arg = str(arg)
                self.add_debug("'%s' is not an int, or not a valid companyID" % arg)
                matches = [x for _,x in self.connection.companies.items() if arg in x.name]
                if len(matches) < 1:
                    self.add_notice("No company matches: '%s'" % arg)
                    continue
                for item in matches:
                    companies[item.id] = item
        format = "%14s %s"
        for item in companies.values():
            data = item.to_dict()
            players = [x for _, x in self.connection.clients.items() if x.play_as == item.id]
            economy = item.economy.to_dict()
            vehicles = item.vehicles.to_dict()
            stations = item.stations.to_dict()
            self.add_line("Company info")
            for key in ('id', 'name', 'manager', 'passworded', 'startyear', 'ai',):
                self.add_line(format % (key, data[key]))
            for key in ('money', ('currentLoan', 'current loan'), 'income'):
                name = key
                if isinstance(key, tuple):
                    key, name = key
                self.add_line(format % (name, economy[key]))
            self.add_line("Vehicles")
            for key in ('train', 'bus', 'lorry', 'plane', 'ship'):
                self.add_line(format % (key, vehicles[key]))
            self.add_line("Stations")
            for key in ('train', 'bus', 'lorry', 'plane', 'ship'):
                self.add_line(format % (key, stations[key]))
            self.add_line("Players")
            for player in players:
                self.add_line(format % (player.id, player.name))

    @command("ping")
    @swallow_args
    def _ping(self):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        self.connection.ping() 

    @command("say", "bcast", "broadcast")
    def _say(self, cmd, args_orig, args):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        for part in textwrap.wrap(args_orig, NETWORK_CHAT_LENGTH):
            self.connection.send_packet(AdminChat, action = Action.CHAT, destType = DestType.BROADCAST, clientID = 0, message = part)
        self.add_chat(origin="SERVER", message = args_orig)

    @command("msg", "cmsg")
    def _msg(self, cmd, args_orig, args):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        if cmd in ("msg",):
            pool = self.connection.clients
            action = Action.CHAT_CLIENT
            desttype = DestType.CLIENT
        elif cmd in ("cmsg",):
            pool = self.connection.companies
            action = Action.CHAT_COMPANY
            desttype = DestType.TEAM
        else:
            return self.add_error("Invalid type")
        parts = args_orig.split(' ', 1)
        if len(parts) != 2:
            return self.add_error("Usage: `%(cmd)s <target> <message>`" % {'cmd': cmd})
        target, message = parts
        target_name = None
        try:
            target = int(target)
            if target not in pool:
                raise ValueError()
            else:
                target_name = pool[target].name
        except ValueError:
            target = str(target)
            matches = [x for _, x in pool if target == x.name]
            if len(matches) > 1:
                return self.add_error("Too many matches, please specify by ID")
            elif not matches:
                return self.add_error("No match found for '%s'" % target)
            target = matches[0].id
            target_name = matches[0].name
        for part in textwrap.wrap(message, NETWORK_CHAT_LENGTH - 1):
            self.connection.send_packet(AdminChat, action = action, destType = desttype, clientID = target, message = part)
        self.add_chat(origin = "SERVER", target = target_name or ' ', message = message)

    @command("rcon")
    def _rcon(self, cmd, args_orig, args):
        if not self.connection.is_connected:
            return self.add_error("NOT_CONNECTED")
        if len(args_orig) >= NETWORK_RCONCOMMAND_LENGTH:
            return self.add_error("RCON Command too long (%d/%d)" % (len(args_orig), NETWORK_RCONCOMMAND_LENGTH))
        self.connection.send_packet(AdminRcon, command = args_orig)
        self.add_chat(origin = "RCON", message = args_orig)


def main(klass=OpenTTDAdmin):
    options, args = parser.parse_args()
    sys.excepthook = except_hook

    main_window = klass(options, args)
    main_window.main()


if __name__ == "__main__":
    main()
