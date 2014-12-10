#!/usr/bin/env python

import os
import re
import sys
import argparse
import importlib


root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

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

# Put extra params in sys.argv so the tasks can get them
sys.argv = [args.task_name + '.py']
sys.argv.extend(args.params)

importlib.import_module('app.tasks.%s' % args.task_name)
