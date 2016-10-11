from datetime import datetime
import time
import os
import sys
import re
import subprocess


def list_all():

    if sys.platform == 'win32':
        # /format:value is used because the standard output format and the csv
        # format have issues with certain process command lines
        proc = subprocess.Popen(
            ['wmic', 'path', 'win32_process', 'get', 'CreationDate,ProcessId,CommandLine', '/format:value'],
            stdout=subprocess.PIPE
        )
        stdout, _ = proc.communicate()

        now = time.time()

        command_line = None
        age = None
        pid = None
        for num, line in enumerate(stdout.decode('utf-8', 'replace').strip().splitlines()):
            line = line.strip()
            if not line:
                continue

            if line.startswith('CommandLine='):
                command_line = line[12:]

            elif line.startswith('CreationDate='):
                value = line[13:]
                # We ignore the timezone offset since that is taken care
                # of by the fact that time.time() is local also
                minus_pos = value.find('-')
                plus_pos = value.find('+')
                if minus_pos != -1 or plus_pos != -1:
                    sign_pos = minus_pos if minus_pos != -1 else plus_pos
                    datestring = value[0:sign_pos]
                else:
                    datestring = value
                start = datetime.strptime(datestring, '%Y%m%d%H%M%S.%f')
                age = now - time.mktime(start.timetuple())

            elif line.startswith('ProcessId='):
                pid = int(line[10:])
                yield (pid, age, command_line)
                pid = None
                age = None
                command_line = None

    elif sys.platform == 'darwin':
        proc = subprocess.Popen(
            ['ps', '-ex', '-o', 'pid=,lstart=,command='],
            stdout=subprocess.PIPE
        )
        stdout, _ = proc.communicate()

        now = time.time()

        for line in stdout.decode('utf-8').splitlines():
            line_match = re.match(
                r'^\s*(\d+)\s+(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(.*)$',
                line
            )
            pid = int(line_match.group(1))
            start = datetime.strptime(line_match.group(2), '%c')
            age = now - time.mktime(start.timetuple())
            command_line = line_match.group(3)
            yield (pid, age, command_line)

    else:
        jiffies_conf_num = os.sysconf_names['SC_CLK_TCK']
        jiffies_per_sec = os.sysconf(jiffies_conf_num)

        with open('/proc/uptime', 'rb') as f:
            fields = f.read().decode('utf-8').split(' ')
            system_start_time = float(fields[0])

        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            try:
                with open(os.path.join('/proc', pid, 'cmdline'), 'rb') as f, \
                        open(os.path.join('/proc', pid, 'stat'), 'rb') as f2:
                    command_line = f.read().replace(b'\x00', b' ').decode('utf-8')
                    stats = f2.read().decode('utf-8')
                    # Consume the pid and comm data since comm is in parens and
                    # may contain spaces
                    pid_comm_match = re.match(r'^\s*\d+\s+\(.*\)\s+', stats)
                    later_stats = stats[len(pid_comm_match.group(0)):].split(' ')
                    # This value is stored in field 22, but we removed the first
                    # two fields, so we reference field 20
                    seconds_since_start = int(later_stats[19]) / jiffies_per_sec
                    age = int(system_start_time - seconds_since_start)

                    yield (int(pid), age, command_line)

            except (IOError, UnicodeDecodeError):
                continue
