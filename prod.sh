#!/bin/bash

./venv/bin/uwsgi -s /var/tmp/uwsgi-packagecontrol.io.socket --uid daemon -H venv -L --module prod -p 8 --master
