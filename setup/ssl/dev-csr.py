#!/usr/bin/env python3

from oscrypto import asymmetric
from csrbuilder import CSRBuilder, pem_armor_csr
from datetime import date


private_key = asymmetric.load_private_key('./secrets/dev.packagecontrol.io.key', None)

builder = CSRBuilder(
    {
        'country_name': 'US',
        'state_or_province_name': 'New Hampshire',
        'locality_name': 'Plymouth',
        'organization_name': 'Codex Non Sufficit LLC',
        'common_name': 'dev.packagecontrol.io',
    },
    private_key.public_key.asn1
)
# Add subjectAltName domains
builder.subject_alt_domains = ['dev.packagecontrol.io']
request = builder.build(private_key)

with open('./secrets/dev.packagecontrol.io-%s.csr' % date.today().year, 'wb') as f:
    f.write(pem_armor_csr(request))
