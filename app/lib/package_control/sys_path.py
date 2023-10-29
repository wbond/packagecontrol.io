# Not shared with Package Control

import os

__cache_path = os.path.join(os.path.expanduser('~'), '.package_control')


def set_cache_dir(cache_path):
    global __cache_path
    __cache_path = cache_path


def pc_cache_dir():
    return __cache_path


def user_config_dir():
    return pc_cache_dir()
