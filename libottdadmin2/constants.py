#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

#
# constant names and values taken from openttd @ src/network/core/config.h
#

NETWORK_DEFAULT_PORT = 3979  # The default port of the game server (TCP & UDP)
NETWORK_ADMIN_PORT = 3977  # The default port for admin network

SEND_MTU = 1460  # Number of bytes we can pack in a single packet

NETWORK_GAME_ADMIN_VERSION = 1  # What version of the admin network do we use?
NETWORK_GAME_INFO_VERSION = 4  # What version of game-info do we use?
NETWORK_COMPANY_INFO_VERSION = 6  # What version of company info is this?
NETWORK_MASTER_SERVER_VERSION = 2  # What version of master-server-protocol do we use?

NETWORK_NAME_LENGTH = 80  # The maximum length of the server name and map name, in bytes including '\0'
NETWORK_COMPANY_NAME_LENGTH = 128  # The maximum length of the company name, in bytes including '\0'
NETWORK_HOSTNAME_LENGTH = 80  # The maximum length of the host name, in bytes including '\0'
NETWORK_SERVER_ID_LENGTH = 33  # The maximum length of the network id of the servers, in bytes including '\0'

# Note: NETWORK_REVISION_LENGTH has been increased to 33. Set to the 15 to maintain compat with older versions
NETWORK_REVISION_LENGTH = 33  # The maximum length of the revision, in bytes including '\0'

NETWORK_PASSWORD_LENGTH = 33  # The maximum length of the password, in bytes including '\0'
NETWORK_CLIENTS_LENGTH = 200  # The maximum length for the list of clients that controls a company, including '\0'
NETWORK_CLIENT_NAME_LENGTH = 25  # The maximum length of a client's name, in bytes including '\0'
NETWORK_RCONCOMMAND_LENGTH = 500  # The maximum length of a rconsole command, in bytes including '\0'
NETWORK_GAMESCRIPT_JSON_LENGTH = 1450  # The maximum length of a gamescript json string, in bytes including '\0'
NETWORK_CHAT_LENGTH = 900  # The maximum length of a chat message, in bytes including '\0'

NETWORK_GRF_NAME_LENGTH = 80  # Maximum length of the name of a GRF
NETWORK_MAX_GRF_COUNT = 62  # Maximum number of GRFs that can be sent.
NETWORK_NUM_LANGUAGES = 36  # Number of known languages (to the network protocol) + 1 for 'any'.

NETWORK_NUM_LANDSCAPES = 4  # The number of landscapes in OpenTTD.
