import glob
import gzip
import os
import re
import time
from urllib.parse import urlparse
from datetime import datetime

import pytz

from .. import config
from ..models import system_stats


settings = config.read('log_files')

pwd = os.getcwd()
os.chdir(settings['location'])

filenames = []
for pattern in settings['patterns']:
    filenames.extend(glob.glob(pattern))
os.chdir(pwd)

five_days_ago_timestamp = time.time() - (5 * 86400)
stats = {}
parsed_files = []

for filename in filenames:
    path = os.path.join(settings['location'], filename)

    # Skip older files
    if os.stat(path).st_mtime < five_days_ago_timestamp:
        continue

    # Skip files that have already been processed
    if system_stats.log_file_previously_parsed(filename):
        continue

    date = None
    date_str = None
    with gzip.open(path, 'r') as log_file:
        for line in log_file:
            line = line.decode('utf-8')

            match = re.match('.*\[(?P<date>[^\]]+)\]\s+"\w+\s+(?P<url>[^"]+?)\sHTTP/\d\.\d"\s+\d+\s+(?P<size>\d+)\s+', line)
            # Some crazy request line that does not contain a valid HTTP request
            if not match:
                match = re.match('.*\[(?P<date>[^\]]+)\]\s+"(?P<url>[^"]*)"\s+\d+\s+(?P<size>\d+)\s+', line)

            date = datetime.strptime(match.group('date'), '%d/%b/%Y:%H:%M:%S %z').astimezone(pytz.utc)
            size = int(match.group('size'))
            pathname = urlparse(match.group('url')).path

            date_str = date.strftime('%Y-%m-%d')
            if date_str not in stats:
                stats[date_str] = {
                    'size': 0,
                    'requests': 0,
                    'paths': {}
                }

            stats[date_str]['requests'] += 1
            stats[date_str]['size'] += size
            if pathname not in stats[date_str]['paths']:
                stats[date_str]['paths'][pathname] = {
                    'size': 0,
                    'requests': 0
                }
            stats[date_str]['paths'][pathname]['requests'] += 1
            stats[date_str]['paths'][pathname]['size'] += size

    parsed_files.append(filename)

# Treat this whole block as a transaction so any errors roll everything back
system_stats.begin()

for date in stats:
    system_stats.update('requests_served', date, stats[date]['requests'])
    system_stats.update('bytes_served', date, stats[date]['size'])

    submit_data = stats[date]['paths'].get('/submit', {})
    system_stats.update('submissions', date, submit_data.get('requests', 0))

    json_bytes = 0
    json_requests = 0
    for path in stats[date]['paths']:
        if re.search('\.json$', path):
            json_data = stats[date]['paths'].get(path, {})
            json_bytes += json_data.get('size', 0)
            json_requests += json_data.get('requests', 0)

    system_stats.update('json_requests_served', date, json_requests)
    system_stats.update('json_bytes_served', date, json_bytes)

for filename in parsed_files:
    system_stats.finished_parsing_log_file(filename)

system_stats.commit()
