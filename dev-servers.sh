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

if [[ ! -d "$PROJ_DIR/data/pgsql/base" ]]; then
    initdb "$PROJ_DIR/data/pgsql"
    createdb -U postgres -E 'UTF-8' package_control
fi

pg_ctl -D "$PROJ_DIR/data/pgsql" -l "$PROJ_DIR/data/logs/pgsql.log" start
redis-server --port 6379
pg_ctl -D "$PROJ_DIR/data/pgsql" stop
