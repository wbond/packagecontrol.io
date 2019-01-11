import os
import yaml

from . import env


def read(name, load_env_key=False):
    """
    Reads a config file

    :param name:
        The name of the config file located in the config/ folder. The
        .yml suffix will automatically be added.

    :param load_env_key:
        If the current env name (dev or prod) should be selected from
        the root config dict, thus returning only a sub-tree.

    :return:
        A dict of the settings
    """

    with open('./config/%s.yml' % name, 'r') as f:
        try:
            # Try to use the libyaml loader
            config = yaml.load(f, Loader=yaml.CLoader)
        except (AttributeError):
            config = yaml.load(f)

    if load_env_key:
        return config[env.name]

    return config


_secrets = None


def read_secret(name, default=None):
    """
    Allows reading a config value that should be kept out of version control
    since they are account keys, etc. These value are provided by setting an
    environmental variable `PACKAGE_CONTROL_SECRETS` to the path of a yaml
    file with the secret values.

    :param name:
        The name of the secret config parameter

    :return:
        The secret config value
    """

    global _secrets

    if not _secrets:
        if 'PACKAGE_CONTROL_SECRETS' in os.environ:
            secrets_file = os.environ['PACKAGE_CONTROL_SECRETS']
        else:
            dirname = os.path.dirname(os.path.abspath(__file__))
            secrets_file = os.path.realpath(os.path.join(dirname, '..',
                'secrets.yml'))

        if not os.path.exists(secrets_file):
            raise Exception(('The secrets file, "%s", does not exists. It ' +
                'can be overridden by the environmental variable ' +
                'PACKAGE_CONTROL_SECRETS.') % secrets_file)

        with open(secrets_file, 'r') as f:
            try:
                # Try to use the libyaml loader
                _secrets = yaml.load(f, Loader=yaml.CLoader)
            except (AttributeError):
                _secrets = yaml.load(f)

    return _secrets.get(name, default)
