#!/usr/bin/env python
#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from collections import defaultdict
from optparse import OptionParser
import socket
import sys
import os
import time

from libottdadmin2.client import AdminClient
from libottdadmin2.packets import *

import logging
logging.basicConfig(level=logging.CRITICAL)

try:
    import json
except ImportError:
    import simplejson as json 

usage = "usage: %prog -p password [options] <json_file>"

parser = OptionParser(usage = usage)
parser.add_option("-H", "--host", dest="host", metavar="HOST",
                  default="127.0.0.1", \
                  help="connect to HOST (default: 127.0.0.1)", )
parser.add_option("-P", "--port", dest="port", type="int", default=3977, 
                  help="use PORT as port (default: 3977)", metavar="PORT")
parser.add_option("-p", "--password", dest="password", default=None,
                  help="use PASS as password", metavar="PASS")
parser.add_option("-q", "--quiet", dest="verbose", action="store_false", 
                  help="surpress output")
#parser.add_option("-Q", "--output-only", dest="output_only", action="store_true", 
#                  help="Output responses only (use in combination with -q)", default=False)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="be verbose (default)", default=True)

if __name__ == "__main__":
    options, args = parser.parse_args()
    if options.password is None:
        parser.error("--password is required")
    if len(args) < 1:
        parser.error("Please specify a JSON file")

    if not os.path.exists(args[0]):
        parser.error("Please specify a JSON file")

    json_file = open(args[0], 'r')
    try:
        json_data = json.load(json_file)
    except ValueError as e:
        parser.error("Specified JSON file is not a valid JSON file: %s" % str(e))
    finally:
        json_file.close()

    if options.verbose:
        print("Loading extra imports:")
    for x in json_data.get("imports", []):
        if options.verbose:
            print("    %s" % x)
            __import__(x)

    formatters = defaultdict(lambda: "%r")

    if options.verbose:
        print("Loading formatters")
    for reg, section in [(send, "send"), (receive, "receive")]:
        for key, format in json_data.get("formatters", {}).get(section,{}).items():
            packet = None
            if isinstance(key, basestring):
                packet = reg.get_by_name(key)
            else:
                try:
                    packet = reg[key]
                except PacketNotFound:
                    pass
            if packet is None:
                print("Unknown packet name in section '%s': %r" % (section, key))
                continue
            formatters[packet.packetID] = format

    def formatter_recv(packet, data):
        pid = packet
        pname = "Unknown packet"
        if not isinstance(pid, (int, long)):
            pid = packet.packetID
            pname = packet.__class__.__name__
        format = formatters[pid]
        print("Received packet with ID: %d (%s)" % (pid, pname))
        print(format % data)

    def formatter_send(packet, origin, **data):
        pid = packet
        pname = "Unknown packet"
        if not isinstance(pid, (int, long)):
            pid = packet.packetID
            pname = packet.__class__.__name__
        format = formatters[pid]
        print("Sending packet with ID: %d (%s)" % (pid, pname))
        print(format % data)

    if options.verbose:
        print("Loading packetlist")

    packets = []

    for item in json_data.get("packets", []):
        packetName = item.get("id", None)
        data = item.get("data", {})
        poll = item.get("poll", [])
        if packetName is None:
            print("Unknown entry: %r" % item)
            continue
        packet = None
        if isinstance(packetName, basestring):
            packet = send.get_by_name(packetName)
        else:
            try:
                packet = send[packetName]
            except PacketNotFound:
                pass
        if packet is None:
            print("Unknown packet name: %r" % packetName)
            continue
        packets.append([packet.__class__, data, poll])

    if options.verbose:
        print("Connecting to %(host)s:%(port)s" % {'host': options.host, 'port': options.port})
    connection = AdminClient()
    connection.packet_recv += formatter_recv
    connection.packet_send += formatter_send
    connection.configure(password=options.password, host=options.host, port=options.port)
    if not connection.connect():
        print("Unable to connect to %(host)s:%(port)s" % {'host': options.host, 'port': options.port})
        sys.exit()

    connection.poll(0.2)
    connection.poll(0.2)

    for packet, data, poll in packets:
        connection.send_packet(packet, **data)
        if not isinstance(poll, (list, tuple)):
            if isinstance(poll, float) and poll > 0:
                poll = [poll,]
            elif isinstance(poll, bool) and poll:
                poll = [1.0,]
        for timeout in poll:
            connection.poll(timeout)

    while(connection.poll(0.25) != False):
        time.sleep(0.1)

    if options.verbose:
        print("Test complete")
    connection.force_disconnect()