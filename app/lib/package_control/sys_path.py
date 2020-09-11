# Not shared with Package Control

import os


def pc_cache_dir():
    return os.path.join(os.path.expanduser('~'), '.package_control')


def user_config_dir():
    return pc_cache_dir()
