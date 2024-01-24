import ed25519

privKey, pubKey = ed25519.create_keypair()
print("Private key = %s" % privKey.to_ascii(encoding='hex').decode('ascii'))
print("Public key  = pubkey-v1:%s" % pubKey.to_ascii(encoding='hex').decode('ascii'))
