import os
import pwd
import sys
import urllib.request
import urllib.parse

from ..lib import ssh
from .. import config
from .. import env

creds = config.read('deploy')
db_creds = config.read('db')['prod']


migration = None
if len(sys.argv) > 1 and sys.argv[1]:
    migration = sys.argv[1]
    migration_path = 'setup/sql/migrations/%s.sql' % migration
    if not os.path.exists(migration_path):
        print('Migration "%s" does not exist' % migration, file=sys.stderr)
        sys.exit(1)


def puts(string, include_newline=True):
    ending = "\n" if include_newline else ""
    print(string, end=ending)
    sys.stdout.flush()

puts('Connecting to %s@%s ... ' % (creds['username'], creds['host']), False)
connection = ssh.SSH(creds['host'], creds['username'])
puts('done')

def try_exec(command):
    puts('> %s' % command)
    code, output = connection.execute(command)
    if code != 0:
        raise Exception(output)
    output = '  ' + output.replace('\n', '  \n')
    if len(output.strip()):
        puts(output)

try:
    try_exec("cd /var/www/%s" % creds['domain'])
    try_exec("git pull --rebase")
    try_exec("git rev-parse HEAD > ./git-sha1.yml")

    if migration:
        try_exec("psql -U %s -d %s -f %s" % (db_creds['user'], db_creds['database'], migration_path))

    # Restart uwsgi workers so new codebase is used
    try_exec("echo r | sudo -u daemon tee /var/tmp/uwsgi-%s.fifo > /dev/null" % creds['domain'])

    # Clear all cached function results in case data structures changed
    try_exec("redis-cli EVAL \"return redis.call('del', unpack(redis.call('keys', ARGV[1])))\" 0 'app.*'")

    puts('Notifying Rollbar of deploy ... ', False)
    post_data = urllib.parse.urlencode({
        'environment': 'production',
        'access_token': config.read_secret('rollbar_key'),
        'local_username': pwd.getpwuid(os.getuid()).pw_name,
        'revision': env.sha1
    })
    request = urllib.request.Request('https://api.rollbar.com/api/1/deploy/')
    request.add_header('Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
    urllib.request.urlopen(request, post_data.encode('utf-8'))
    puts('done')

finally:
    connection.close()
