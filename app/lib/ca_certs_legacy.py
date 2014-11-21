import hashlib
import os
import re

from .package_control.cmd import Cli
from .package_control.ca_certs import get_system_ca_bundle_path
from .package_control.open_compat import open_compat, read_compat



def find_root_ca_cert(settings, domain):
    runner = OpensslCli(settings.get('openssl_binary'), settings.get('debug'))
    binary = runner.retrieve_binary()

    args = [binary, 's_client', '-showcerts', '-connect', domain + ':443']
    result = runner.execute(args, os.path.dirname(binary))

    certs = []
    temp = []

    in_block = False
    for line in result.splitlines():
        if line.find('BEGIN CERTIFICATE') != -1:
            in_block = True
        if in_block:
            temp.append(line)
        if line.find('END CERTIFICATE') != -1:
            in_block = False
            certs.append(u"\n".join(temp))
            temp = []

    # Grabbing the certs for the domain failed, most likely because it is down
    if not certs:
        return [False, False]

    # Remove the cert for the domain itself, just leaving the
    # chain cert and the CA cert
    certs.pop(0)

    # Look for the "parent" root CA cert
    subject = openssl_get_cert_subject(settings, certs[-1])
    issuer = openssl_get_cert_issuer(settings, certs[-1])

    cert = get_ca_cert_by_subject(settings, issuer)
    cert_hash = hashlib.md5(cert.encode('utf-8')).hexdigest()

    return [cert, cert_hash]


def get_ca_cert_by_subject(settings, subject):
    bundle_path = get_system_ca_bundle_path(settings)

    with open_compat(bundle_path, 'r') as f:
        contents = read_compat(f)

    temp = []

    in_block = False
    for line in contents.splitlines():
        if line.find('BEGIN CERTIFICATE') != -1:
            in_block = True

        if in_block:
            temp.append(line)

        if line.find('END CERTIFICATE') != -1:
            in_block = False
            cert = u"\n".join(temp)
            temp = []

            if openssl_get_cert_subject(settings, cert) == subject:
                return cert

    return False


def openssl_get_cert_issuer(settings, cert):
    """
    Uses the openssl command line client to extract the issuer of an x509
    certificate.
    :param settings:
        A dict to look in for `debug` and `openssl_binary` keys
    :param cert:
        A string containing the PEM-encoded x509 certificate to extract the
        issuer from
    :return:
        The cert issuer
    """

    runner = OpensslCli(settings.get('openssl_binary'), settings.get('debug'))
    binary = runner.retrieve_binary()
    args = [binary, 'x509', '-noout', '-issuer']
    output = runner.execute(args, os.path.dirname(binary), cert)
    return re.sub('^issuer=\s*', '', output)


def openssl_get_cert_name(settings, cert):
    """
    Uses the openssl command line client to extract the name of an x509
    certificate. If the commonName is set, that is used, otherwise the first
    organizationalUnitName is used. This mirrors what OS X uses for storing
    trust preferences.
    :param settings:
        A dict to look in for `debug` and `openssl_binary` keys
    :param cert:
        A string containing the PEM-encoded x509 certificate to extract the
        name from
    :return:
        The cert subject name, which is the commonName (if available), or the
        first organizationalUnitName
    """

    runner = OpensslCli(settings.get('openssl_binary'), settings.get('debug'))

    binary = runner.retrieve_binary()

    args = [binary, 'x509', '-noout', '-subject', '-nameopt',
        'sep_multiline,lname,utf8']
    result = runner.execute(args, os.path.dirname(binary), cert)

    # First look for the common name
    cn = None
    # If there is no common name for the cert, the trust prefs use the first
    # orginizational unit name
    first_ou = None

    for line in result.splitlines():
        match = re.match('^\s+commonName=(.*)$', line)
        if match:
            cn = match.group(1)
            break
        match = re.match('^\s+organizationalUnitName=(.*)$', line)
        if first_ou is None and match:
            first_ou = match.group(1)
            continue

    # This is the name of the cert that would be used in the trust prefs
    return cn or first_ou


def openssl_get_cert_subject(settings, cert):
    """
    Uses the openssl command line client to extract the subject of an x509
    certificate.
    :param settings:
        A dict to look in for `debug` and `openssl_binary` keys
    :param cert:
        A string containing the PEM-encoded x509 certificate to extract the
        subject from
    :return:
        The cert subject
    """

    runner = OpensslCli(settings.get('openssl_binary'), settings.get('debug'))
    binary = runner.retrieve_binary()
    args = [binary, 'x509', '-noout', '-subject']
    output = runner.execute(args, os.path.dirname(binary), cert)
    return re.sub('^subject=\s*', '', output)


class OpensslCli(Cli):

    cli_name = 'openssl'

    def retrieve_binary(self):
        """
        Returns the path to the openssl executable
        :return: The string path to the executable or False on error
        """

        name = 'openssl'
        if os.name == 'nt':
            name += '.exe'

        binary = self.find_binary(name)
        if binary and os.path.isdir(binary):
            full_path = os.path.join(binary, name)
            if os.path.exists(full_path):
                binary = full_path

        if not binary:
            show_error((u'Unable to find %s. Please set the openssl_binary ' +
                u'setting by accessing the Preferences > Package Settings > ' +
                u'Package Control > Settings \u2013 User menu entry. The ' +
                u'Settings \u2013 Default entry can be used for reference, ' +
                u'but changes to that will be overwritten upon next upgrade.') % name)
            return False

        return binary
