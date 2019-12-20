# SSL Scripts

These scripts generate keys and certificate signing requests for the SSL
certs used on packagecontrol.io and dev.packagecontrol.io.

The dependencies can be installed by running:

```bash
pip install -r requirements
```

## Production Environment

Generate a new private key:

```bash
./key.py
```

Generate a new CSR:

```bash
./csr.py
```

## Development Environment

Generate a new private key:

```bash
./dev-key.py
```

Generate a new CSR:

```bash
./dev-csr.py
```
