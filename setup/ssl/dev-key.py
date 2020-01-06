#!/usr/bin/env python3

from oscrypto import asymmetric

pub, priv = asymmetric.generate_pair('rsa', 2048)

with open('./secrets/dev.packagecontrol.io.key', 'wb') as f:
    f.write(asymmetric.dump_openssl_private_key(priv, None))

with open('./secrets/dev.packagecontrol.io.pub', 'wb') as f:
    f.write(asymmetric.dump_public_key(pub))
