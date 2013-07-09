#!/usr/bin/env python

from optparse import OptionParser
import socket
from libottdadmin2.client import AdminConnection, AdminRcon

usage = "usage: %prog -p password [options] \"command1\" [\"command2\"] [...]"

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
parser.add_option("-Q", "--output-only", dest="output_only", action="store_true", 
                  help="Output responses only (use in combination with -q)", default=False)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="be verbose (default)", default=True)


if __name__ == "__main__":
    options, args = parser.parse_args()
    if options.password is None:
        parser.error("--password is required")
    if len(args) < 1:
        parser.error("At least one command is required")

    if options.verbose:
        print("Connecting to %(host)s:%(port)s" % {'host': options.host, 'port': options.port})

    connection = AdminConnection(password=options.password)
    connection.settimeout(0.2)
    connection.connect(options.host, options.port)
    failed = False
    try:
        protocol_response = connection.recv_packet()
        welcome_response = connection.recv_packet()
    except socket.error:
        failed = True

    if protocol_response is None or welcome_response is None:
        failed = True

    if failed:
        print("Unable to connect to %(host)s:%(port)s" % {'host': options.host, 'port': options.port})
    else:
        for command in args:
            if options.verbose:
                print("Sending Rcon command: '%s'" % command)
            connection.send_packet(AdminRcon, command = command)
            while True:
                try:
                    response = connection.recv_packet()
                    if response and (options.verbose or options.output_only):
                        print(">>> %s" % response[1]['result'])
                except socket.error:
                    break

    if options.verbose:
        print("Disconnecting")
    connection.disconnect()    
