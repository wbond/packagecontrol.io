#!/usr/bin/env python

import os
import re
import sys
import argparse
import importlib
from app.lib import processes
from app import env


root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

logs_root = os.path.join(root_dir, 'task_logs')

tasks_root = os.path.join(root_dir, 'app/tasks')
valid_tasks = []
for filename in os.listdir(tasks_root):
    if filename == '__init__.py':
        continue
    valid_tasks.append(re.sub('\.py', '', filename))

parser = argparse.ArgumentParser(description='Run a task from app/tasks/')
parser.add_argument('task_name', choices=valid_tasks)
parser.add_argument('params', nargs='*')

args = parser.parse_args()

# Make sure we aren't doubling up tasks without using a pid file that can
# get stuck. This currently only supports OS X and Linux.
current_pid = os.getpid()
for pid, command_line in processes.list_all():
    if pid == current_pid:
        continue
    match = re.match('^(.*?[/ ]tasks\\.py)\\s+(\\w+)(\\s+(.*))?$', command_line)
    if not match:
        continue
    if match.group(2) == args.task_name:
        print('Another instance of the %s task is currently running' % args.task_name)
        sys.exit(0)

if env.is_prod():
    for num in range(10, 0, -1):
        source_file = os.path.join(logs_root, '%s.%d.log' % (args.task_name, num - 1))
        dest_file = os.path.join(logs_root, '%s.%d.log' % (args.task_name, num))
        if os.path.exists(source_file):
            os.rename(source_file, dest_file)

    log_file = os.path.join(logs_root, '%s.0.log' % args.task_name)
    sys.stdout = open(log_file, 'w', encoding='utf-8')

# Put extra params in sys.argv so the tasks can get them
sys.argv = [args.task_name + '.py']
sys.argv.extend(args.params)

importlib.import_module('app.tasks.%s' % args.task_name)
