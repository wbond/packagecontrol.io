# Development Environment

This site is built using Python 3.6.8, PostgreSQL 11, Redis and Nginx.

In addition, to install the lxml package, the following C libraries' development
header are necessary to be installed. Here are some example commands:

```bash
apt-get install libxml2-dev libxslt-dev
yum install libxml2-devel libxslt-devel
pacaur -S libxml2 libxslt
```

To work on this project you may need a C compiler since some of the packages
have C components, and some may not be available as wheels.

Additionally, nodejs must be installed since the JS on the site is
(unfortunately) written in coffeescript.

## Virtualenv Setup

Set up the virtualenv and install the packages:

```bash
python -m venv venv
. venv/bin/active
pip install -r setup/requirements.txt
pip install -r setup/dev-requirements.txt
```

## Basic Usage

Run the server:

```bash
python dev.py
```

Start the compiler to automatically compile `.coffee` and `.scss` files:

```bash
python compile.py
```

Whenever one of these files is saved, the resulting JS or CSS files will be
regenerated.

## Tmux Script

There exists a tmux script that opens multiple panes with the server,
compiler, a terminal for git and a PostgreSQL CLI connection. To use this,
make sure you have tmux installed and execute:

```bash
./dev.sh
```
