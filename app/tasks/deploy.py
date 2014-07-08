import sys

from ..lib import ssh
from .. import config

creds = config.read('deploy')

print('Connecting to %s@%s ... ' % (creds['username'], creds['host']), end='')
sys.stdout.flush()
connection = ssh.SSH(creds['host'], creds['username'])
print('done')

def try_exec(command):
    print('> %s' % command)
    code, output = connection.execute(command)
    if code != 0:
        raise Exception(output)
    output = '  ' + output.replace('\n', '  \n')
    if len(output.strip()):
        print(output)

try:
    try_exec("cd /var/www/sublime.wbond.net")
    try_exec("git pull --rebase")
    try_exec("echo r | sudo -u daemon tee /var/tmp/uwsgi-sublime.wbond.net.fifo > /dev/null")
finally:
    connection.close()
