import sys

from ..lib import ssh
from .. import config

creds = config.read('deploy')

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
    try_exec("cd /var/www/sublime.wbond.net")
    try_exec("git pull --rebase")
    try_exec("git rev-parse HEAD > ./git-sha1.yml")
    try_exec("echo r | sudo -u daemon tee /var/tmp/uwsgi-sublime.wbond.net.fifo > /dev/null")
finally:
    connection.close()
