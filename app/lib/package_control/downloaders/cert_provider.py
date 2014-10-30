# Not shared with Package Control
from ..ca_certs import get_system_ca_bundle_path


class CertProvider(object):
    """
    A base downloader that provides access to a ca-bundle for validating
    SSL certificates.
    """

    def check_certs(self, domain, timeout):
        """
        Ensures that the SSL CA cert for a domain is present on the machine

        :param domain:
            The domain to ensure there is a CA cert for

        :param timeout:
            The int timeout for downloading the CA cert from the channel

        :return:
            The CA cert bundle path on success, or False on error
        """

        # Try to use the system CA bundle
        ca_bundle_path = get_system_ca_bundle_path(self.settings)
        if ca_bundle_path:
            return ca_bundle_path

        return '/etc/ssl/certs/ca-certificates.crt'
