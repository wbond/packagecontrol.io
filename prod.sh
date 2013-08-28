#!/bin/bash

./venv/bin/uwsgi -s /var/tmp/uwsgi-sublime.wbond.net.socket --uid daemon -H venv -L --module prod -p 8 --master
