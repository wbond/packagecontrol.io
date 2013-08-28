# Not shared with Package Control


class ReleaseSelector():
    """
    A base class for finding the best version of a package for the current machine
    """

    def select_release(self, package_info):
        """
        Returns an un-modified package info dict for package from package schema version 2.0

        :param package_info:
            A package info dict with a "releases" key

        :return:
            A copy of the package info dict that was passed in
        """

        new_releases = []
        for release in package_info['releases']:
            # Make sure we have these two keys
            if 'platforms' not in release:
                release['platforms'] = ['*']
            if 'sublime_text' not in release:
                release['sublime_text'] = '*'
            # Make sure the platform info is a list
            if not isinstance(release['platforms'], list):
                release['platforms'] = [release['platforms']]
            if 'url' in release:
                release['url'] = release['url'].replace('https://nodeload.github.com/', 'https://codeload.github.com/')
            new_releases.append(release)
        package_info['releases'] = new_releases

        return package_info

    def select_platform(self, package_info):
        """
        Returns a modified package info dict for package from package schema version <= 1.2

        :param package_info:
            A package info dict with a "platforms" key

        :return:
            The package info dict with the "platforms" key deleted, and replaced by a
            "releases" key that is compatible with schema version 2.0
        """

        releases = []

        for platform in package_info['platforms']:
            details = package_info['platforms'][platform][0]
            releases.append({
                'platforms': [platform],
                # Schema 1.2 only ever worked for ST2
                'sublime_text': '<3000',
                'version': details['version'],
                'url': details['url'].replace('https://nodeload.github.com/', 'https://codeload.github.com/'),
                # If no date is specified, use a date from around when
                # Package Control was first released
                'date': package_info.get('last_modified', '2011-08-01 00:00:00')
            })

        package_info['releases'] = releases
        del package_info['platforms']

        return package_info
