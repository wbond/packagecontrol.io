import os


name = 'dev'
if 'PACKAGE_CONTROL_ENV' in os.environ:
    name = os.environ['PACKAGE_CONTROL_ENV']


def is_dev():
    return name == 'dev'


def is_prod():
    return name == 'prod'
