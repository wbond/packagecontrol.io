import os
import sys
import re
import subprocess


def list_all():

    if sys.platform == 'win32':
        raise EnvironmentError('Listing processes is currently not supported on Windows')

    elif sys.platform == 'darwin':
        proc = subprocess.Popen(
            ['ps', '-ex', '-o', 'pid=,command='],
            stdout=subprocess.PIPE
        )
        stdout, _ = proc.communicate()

        for line in stdout.decode('utf-8').splitlines():
            line_match = re.match('^\\s*(\\d+)\\s+(.*)$', line)
            pid = int(line_match.group(1))
            command_line = line_match.group(2)
            yield (pid, command_line)

    else:
        current_pid = os.getpid()
        for pid in os.listdir('/proc'):
            if not pid.isdigit() or int(pid) == current_pid:
                continue
            try:
                with open(os.path.join('/proc', pid, 'cmdline'), 'rb') as f:
                    command_line = f.read().decode('utf-8')
                    yield (int(pid), command_line)

            except (IOError, UnicodeDecodeError):
                continue
