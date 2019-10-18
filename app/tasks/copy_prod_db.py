import subprocess
import sys
import warnings

from ..lib import ssh
from ..lib.ssh import try_exec
from ..lib.output import puts
from .. import config
from .. import env


warnings.filterwarnings(action='ignore',module='.*paramiko.*')


def local_exec(command):
    puts('< %s' % command)
    proc = subprocess.Popen(
        command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    output, _ = proc.communicate()
    code = proc.returncode
    if code != 0:
        raise Exception(output)
    output = '  ' + output.decode('utf-8').replace('\n', '\n  ')
    if len(output.strip()):
        puts(output)


creds = {
    'user': 'root',
    'host': 'packagecontrol.io',
    'home': '/root'
}

puts('Connecting to %s@%s ... ' % (creds['user'], creds['host']), False)
conn = ssh.SSH(creds['host'], creds['user'])
puts('done')

try:
    tmp_path = env.root

    try_exec(conn, "pg_dump -U postgres -F c -s -f %s/package_control-schema.dmp package_control" % creds['home'])
    try_exec(conn, "pg_dump -U postgres -F d -j 2 -a -T usage -T unique_package_installs -T ips -f %s/package_control-data package_control" % creds['home'])
    local_exec("scp %s@%s:%s/package_control-schema.dmp %s/" % (creds['user'], creds['host'], creds['home'], tmp_path))
    local_exec("scp -r %s@%s:%s/package_control-data %s/package_control-data" % (creds['user'], creds['host'], creds['home'], tmp_path))
    try_exec(conn, "rm %s/package_control-schema.dmp" % creds['home'])
    try_exec(conn, "rm -r %s/package_control-data" % creds['home'])
    local_exec("dropdb -U postgres package_control")
    local_exec("createdb -U postgres -E UTF-8 package_control")
    local_exec("pg_restore -U postgres -d package_control -F c -s %s/package_control-schema.dmp" % tmp_path)
    local_exec("pg_restore -U postgres -d package_control -F d -j 2 -a --disable-triggers %s/package_control-data" % tmp_path)
    local_exec('rm %s/package_control-schema.dmp' % tmp_path)
    local_exec('rm -r %s/package_control-data' % tmp_path)

    puts('done')

finally:
    conn.close()
