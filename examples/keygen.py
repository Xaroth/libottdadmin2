from monocypher import generate_key, compute_key_exchange_public_key

secret_key = generate_key()
public_key = compute_key_exchange_public_key(secret_key)

print("This is the secret key. It must not be shared and is used as command line argument for the client. It must be kept secret.")
print(secret_key.hex())
print()

print("This is the associated public key. It may be shared and can be placed in the '[admin_authorized_keys]' section of OpenTTD's private.cfg of the server.")
print(public_key.hex())
print()
