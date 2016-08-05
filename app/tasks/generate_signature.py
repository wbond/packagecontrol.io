from oscrypto import asymmetric
from asn1crypto import pem, keys
import os

from .. import config

root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
assets = os.path.join(root, 'assets')

pc_path = os.path.join(assets, 'Package Control.sublime-package')
pc_sig_path = os.path.join(assets, 'Package Control.sublime-package.sig')

public_key_pem = config.read('signing')['public_key']
public_key = asymmetric.load_public_key(public_key_pem.encode('ascii'))
private_key_pem = config.read_secret('private_key')
private_key = asymmetric.load_private_key(private_key_pem.encode('ascii'), None)

with open(pc_sig_path, 'wb') as wf, open(pc_path, 'rb') as rf:
    pc_data = rf.read()
    sig = asymmetric.ecdsa_sign(private_key, pc_data, 'sha256')
    asymmetric.ecdsa_verify(public_key, sig, pc_data, 'sha256')
    wf.write(pem.armor('PACKAGE CONTROL SIGNATURE', sig))
    print('Signature written to %s' % pc_sig_path)
