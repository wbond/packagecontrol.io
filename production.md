# Production Environment

The production mode uses uwsgi, which means it does not run on Windows.
Additionally, it uses redis for database result caching, which also does not
run on Windows. The development environment caches results in memory, so
redis is not required.

The required python packages can be installed following the directions from
[development.md](development.md).

In production mode, the app will try to read `./secrets.yml` to load in the
GitHub application keys and the Rollbar account information for error tracking.
The [secrets-example.yml](secrets-example.yml) file has the format and links
to sign up for the free accounts necessary.

To compile the JS and CSS for production usage, run the following:

```
python compile.py prod
```

This will create the necessary minified JS and CSS files in the `public/`
folder.

To start the app in production mode, run:

```
bash prod.sh
```

This will start up a number of workers on a unix socket at
`/var/tmp/uwsgi-packagecontrol.io.socket` using the uwsgi
protocol. You’ll need to run nginx or Apache in front and proxy the
request to uwsgi.

Nginx includes uwsgi support by default, so proxying is as simple as:

```
server {
    listen 80;
    server_name packagecontrol.io;

    root /path/to/packagecontrol.io;

    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/plain text/css application/json text/javascript application/x-javascript text/xml application/xml application/xml+rss image/svg+xml;

    try_files /public/$uri /app/html/$uri @uwsgi;

    location @uwsgi {
        uwsgi_pass  unix:/var/tmp/uwsgi-packagecontrol.io.socket;
        include     uwsgi_params;
    }
}
```
