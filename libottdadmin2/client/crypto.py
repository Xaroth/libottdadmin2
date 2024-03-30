#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from typing import Tuple, Optional

from libottdadmin2.util import loggable
from libottdadmin2.enums import AuthenticationMethod

from monocypher import Blake2b, compute_key_exchange_public_key, generate_key, IncrementalAuthenticatedEncryption, key_exchange, lock, wipe
from os import urandom

MAC_SIZE = 16 # Number of bytes for the message authentication code.
NONCE_SIZE = 24 # Number of bytes for a nonce (random single use token).
PUBLIC_KEY_SIZE = 32 # Number of bytes for a public key.
HEX_SECRET_KEY_LENGTH = 64 # Size of the secret key as hexadecimal string.

@loggable
class CryptoHandler:
    __password = None # Type: bytes
    __our_secret_key = None # Type: bytes
    __our_public_key = None # Type: bytes
    __their_public_key = None # Type: bytes
    __shared_keys = None # Type: bytes
    __key_exchange_nonce = None # Type: bytes
    __methods = 0

    def __init__(self, password: Optional[str] = None, secret_key: Optional[str] = None):
        """Create the crypto handler with the given password and secret key.

        When the password is set, it must not be empty. Setting the password enables
        X25519 password authenticated key exchange.
        When the secret key is set, it must be exactly 64 hexadecimal characters. Setting
        the secret key enables X25519 authorized key authentication. Not setting the
        secret key causes a new random secret key to be generated for this handler.

        Note: when neither a password nor secret key are given, this handler will not have
        any available authentication methods and any attempt of authentication will fail.

        :param password: Optional password to enable password authentication.
        :param secret_key: Optional secret key for authorized key authentication.
        """
        if password:
            if len(password) == 0:
                raise ValueError("The password must not be empty")
            self.__methods |= 1 << AuthenticationMethod.X25519_PAKE
        if secret_key:
            if len(secret_key) != HEX_SECRET_KEY_LENGTH:
                raise ValueError("The hexadecimal secret-key must be exactly %d characters, is was %d characters" % (HEX_SECRET_KEY_LENGTH, len(secret_key)))
            self.__methods |= 1 << AuthenticationMethod.X25519_AUTHORIZED_KEY

        self.__password = bytes(password, 'utf-8')
        self.__our_secret_key = generate_key() if secret_key is None else bytes.fromhex(secret_key)
        self.__our_public_key = compute_key_exchange_public_key(self.__our_secret_key)

    def get_available_methods(self) -> int:
        """Get the authentication methods that this handler is configured for as bitmask."""
        return self.__methods

    def get_our_public_key(self) -> bytes:
        """Get the public key associated with the private key of this handler."""
        return self.__our_public_key

    def get_encryption_handler(self, encryption_nonce: bytes) -> IncrementalAuthenticatedEncryption:
        """Get the handler for performing the encryption for sending data to the server"""
        return IncrementalAuthenticatedEncryption(
            key = self.__shared_keys[:32],
            nonce = encryption_nonce
        )

    def get_decryption_handler(self, encryption_nonce: bytes) -> IncrementalAuthenticatedEncryption:
        """Get the handler for performing the decryption of received data from the server"""
        return IncrementalAuthenticatedEncryption(
            key = self.__shared_keys[32:],
            nonce = encryption_nonce
        )

    def __x25519_auth(self, payload: bytes) -> Tuple[bytes, bytes]:
        shared_secret = key_exchange(self.__our_secret_key, self.__their_public_key)

        digest = Blake2b(hash_size = 64)
        digest.update(shared_secret)
        digest.update(self.__their_public_key) # The server's public key
        digest.update(self.__our_public_key) # The client's public key
        digest.update(payload)
        self.__shared_keys = digest.finalize()

        wipe(shared_secret)

        return lock(
            key = self.__shared_keys[:32],
            nonce = self.__key_exchange_nonce,
            message = urandom(8),
            associated_data = self.__our_public_key
        )

    def on_auth_request(self, method: int, their_public_key: bytes, key_exchange_nonce: bytes) -> Tuple[bytes, bytes]:
        """Create the reply of the key exchange for an authentication request.

        This currently supports X25519 password authenticated key exchange, which uses the password
        locally to construct the shared key between the client and server, and using the message
        authentication code the server can check whether the client knows the password without ever
        sending the password over the network. Next to this there is X25519 authorized key, which
        uses our secret key to do the key exchange and create the shared secret, and using the
        message authentication code the server can check whether the public key the client sends
        is associated with the client's secret key. After this the server checks whether our public
        key is in their list of allowed/authorized keys to login (without password).

        :param method: The authentication method to perform.
        :param their_public_key: The public key as received from the server.
        :param key_exchange_nonce: The nonce, or one time token, as generated by the server for the key exchange.

        :return: Tuple with the MAC (message authentication code) and ciphertext, or None on an error.
        """
        self.__their_public_key = their_public_key
        self.__key_exchange_nonce = key_exchange_nonce

        if (self.__methods & (1 << method)) == 0:
            self.log.error("Received method that was not requested")
            return None;

        if method == AuthenticationMethod.X25519_PAKE:
            self.log.debug("Authenticating using password authenticated key exchange")
            return self.__x25519_auth(self.__password)

        if method == AuthenticationMethod.X25519_AUTHORIZED_KEY:
            self.log.debug("Authenticating using authorized key")
            return self.__x25519_auth(bytes())

        self.log.error("Unknown method")
        return None
