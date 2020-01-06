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

TASK="$1"

if [[ $TASK == "start" ]]; then
    echo "PROJ_DIR: $PROJ_DIR"

    mkdir -p "$PROJ_DIR/data/pgsql"
    mkdir -p "$PROJ_DIR/data/redis"
    mkdir -p "$PROJ_DIR/data/logs"
    mkdir -p "$PROJ_DIR/data/nginx"
    mkdir -p "$PROJ_DIR/data/ssl"

    OLD_REDIS_PID=$(ps awx | grep redis-server | grep -v redis-server | awk '{print $1}')
    if [[ "$OLD_REDIS_PID" -ne "" ]]; then
        redis-cli -h 127.0.0.1 -p 6379 shutdown
    fi

    OLD_PGSQL_PID=$(ps awx | grep postmaster | grep -v postmaster | awk '{print $1}')
    if [[ "$OLD_PGSQL_PID" -ne "" ]]; then
        pg_ctl -s -D "$PROJ_DIR/data/pgsql" stop
    fi

    if [[ ! -f "$PROJ_DIR/data/ssl/dhparam.pem" ]]; then
        echo -n "Generating dhparam for TLS ..."
    	openssl dhparam -out $PROJ_DIR/data/ssl/dhparam.pem 2048
        echo " done"
    fi

    HAS_DB=1
    if [[ ! -e "$PROJ_DIR/data/pgsql/PG_VERSION" ]]; then
        HAS_DB=0
        echo -n "Creating postgresql cluster ..."
        initdb -U postgres -E UTF-8 -D "$PROJ_DIR/data/pgsql"
        echo " done"
    fi

    echo -n "Starting postgresql ..."
    pg_ctl -s -D "$PROJ_DIR/data/pgsql" -l "$PROJ_DIR/data/logs/pgsql.log" start
    echo " done"

    if ((!HAS_DB)); then
        echo -n "Creating initial database ..."
        createdb -U postgres -E UTF-8 package_control
        echo " done"
    fi

    echo -n "Starting redis ..."
    redis-server --port 6379 --daemonize yes --loglevel warning --logfile $PROJ_DIR/data/logs/redis.log
    echo " done"

    NGINX_CONF=$(cat <<SETVAR
    daemon on;

    pid $PROJ_DIR/data/nginx/nginx.pid;
    worker_processes  1;
    error_log $PROJ_DIR/data/logs/nginx-error.log;

    user  wbond staff;

    events {}

    http {
        types {
            text/html                                        html;
            text/css                                         css;
            text/xml                                         xml;
            image/jpeg                                       jpeg jpg;
            application/javascript                           js;
            image/png                                        png;
            image/svg+xml                                    svg svgz;
            image/x-icon                                     ico;
        }

        default_type  text/html;
        access_log $PROJ_DIR/data/logs/nginx.log;

        lua_package_path "$PROJ_DIR/realtime/?.lua;;";
        lua_shared_dict locks 100k;
        lua_shared_dict file_upload 1m;
        lua_max_pending_timers 64;
        init_worker_by_lua_file "$PROJ_DIR/realtime/worker_job.lua";

        server {
            listen       443 ssl http2;
            server_name  dev.packagecontrol.io;

			ssl_certificate  $PROJ_DIR/data/ssl/fullchain.pem;
			ssl_certificate_key  $PROJ_DIR/data/ssl/privkey.pem;
			ssl_dhparam  $PROJ_DIR/data/ssl/dhparam.pem;
			ssl_protocols  TLSv1.2 TLSv1.1 TLSv1;
			ssl_ciphers  'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS';
			ssl_prefer_server_ciphers  on;
			ssl_session_timeout  5m;

			ssl_stapling  on;
			ssl_stapling_verify  on;
			ssl_trusted_certificate  $PROJ_DIR/data/ssl/fullchain.pem;

            root  $PROJ_DIR/public;

            try_files  /assets/\$uri  /public/\$uri  @site;

            location /submit {
                try_files  /assets/\$uri @site;
                access_by_lua_file  "$PROJ_DIR/realtime/record_usage.lua";
            }

            location /channel_v3.json {
                if (\$http_accept_encoding ~ bzip2) {
                    rewrite  ^(/channel_v3.json)$  \$1.bz2  last;
                }
                try_files  /assets/\$uri /public/\$uri @site;
                access_by_lua_file  "$PROJ_DIR/realtime/record_channel.lua";
            }

            location /channel_v3.json.bz2 {
                try_files  /assets/\$uri /public/\$uri @site;
                access_by_lua_file  "$PROJ_DIR/realtime/record_channel.lua";
                header_filter_by_lua '
                    ngx.header["Content-Type"] = "application/json"
                    ngx.header["Content-Encoding"] = "bzip2"
                    ngx.header["Vary"] = "Accept-Encoding"
                ';
            }

            location /realtime {
                lua_socket_log_errors  off;
                content_by_lua_file  "$PROJ_DIR/realtime/stats.lua";
            }

            location ~ ^/.*\.html$ {
                try_files  /app/html/\$uri  @site;
                access_by_lua_file  "$PROJ_DIR/realtime/record_web.lua";
                header_filter_by_lua  '
                    if not app_version then
                        app_version = io.open("$PROJ_DIR/version.yml", "r"):read()
                    end
                    ngx.header["X-App-Version"] = app_version
                ';
            }

            location ~ ^/readmes/img/ {
                try_files  \$uri  @site;
            }

            location @site {
                access_by_lua_file  "$PROJ_DIR/realtime/record_web.lua";
                proxy_pass http://localhost:9000;
                proxy_set_header X-Forwarded-Proto https;
                proxy_set_header X-Forwarded-Host  dev.packagecontrol.io;
                proxy_set_header X-Real-IP         \$remote_addr;
                proxy_set_header X-Forwarded-For   \$remote_addr;
                sub_filter "https://dev.packagecontrol.io" "http://localhost:9000";
                sub_filter "dev.packagecontrol.io" "localhost:9000";
                sub_filter_once off;
            }
        }
    }
SETVAR
    )
    echo "$NGINX_CONF" > $PROJ_DIR/data/nginx/nginx.conf

    echo "Starting nginx (as root)"
    sudo nginx -c $PROJ_DIR/data/nginx/nginx.conf
fi

if [[ $TASK == "stop" ]]; then
    echo "Stopping nginx, redis and postgresql"
    sudo nginx -c $PROJ_DIR/data/nginx/nginx.conf -s stop
    redis-cli -h 127.0.0.1 -p 6379 shutdown
    pg_ctl -s -D "$PROJ_DIR/data/pgsql" stop
fi
