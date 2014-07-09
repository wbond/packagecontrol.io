#!/usr/bin/env python

import os
import re
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

args = parser.parse_args()

importlib.import_module('app.tasks.%s' % args.task_name)
