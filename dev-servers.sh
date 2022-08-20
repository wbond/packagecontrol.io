#!/usr/bin/env bash

set -e

# Figure out what directory this script is in
SCRIPT="$0"
if [[ $(readlink $SCRIPT) != "" ]]; then
    SCRIPT=$(dirname $SCRIPT)/$(readlink $SCRIPT)
fi
if [[ $0 = ${0%/*} ]]; then
    SCRIPT=$(pwd)/$0
fi
PROJ_DIR=$(cd ${SCRIPT%/*} && pwd -P)
echo "PROJ_DIR: $PROJ_DIR"

mkdir -p "$PROJ_DIR/data/pgsql"
mkdir -p "$PROJ_DIR/data/redis"
mkdir -p "$PROJ_DIR/data/logs"

# Create run directory with elevated privileges
PGSQL_RUN_DIR=/var/run/postgresql
if [[ ! -d "$PGSQL_RUN_DIR" ]]; then
    sudo mkdir -p "$PGSQL_RUN_DIR"
    sudo chown $(whoami) "$PGSQL_RUN_DIR"
fi

HAS_DB=1
if [[ ! -e "$PROJ_DIR/data/pgsql/PG_VERSION" ]]; then
    HAS_DB=0
    initdb -U postgres -E UTF-8 -D "$PROJ_DIR/data/pgsql"
    sleep 1
fi

pg_ctl -D "$PROJ_DIR/data/pgsql" -l "$PROJ_DIR/data/logs/pgsql.log" start

if ((!HAS_DB)); then
    createdb -U postgres -E UTF-8 package_control
    psql -U postgres -d package_control -f "$PROJ_DIR/setup/sql/up.sql"
fi

redis-server --port 6379 --daemonize yes --loglevel warning --logfile $PROJ_DIR/data/logs/redis.log

# enter sql shell
psql -U postgres package_control

# shutdown servers
redis-cli -h 127.0.0.1 -p 6379 shutdown
pg_ctl -D "$PROJ_DIR/data/pgsql" stop
