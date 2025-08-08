import re
import json
import hashlib

from ..console_write import console_write


class CachingDownloader:

    """
    A base downloader that will use a caching backend to cache HTTP requests
    and make conditional requests.
    """

    def is_cache_fresh(self, url):
        """
        Determines if cache fresh.

        :param url:
            The url of the request
        :param max_age:
            The maximum age of a cache until it is considdered fresh.

        :returns:
            True if cache is still fresh.
        """
        cache = self.settings.get('cache')
        if not cache:
            return False

        info_key = self.generate_key(url)
        age = cache.age(info_key)
        is_fresh = age < self.settings.get('max_age', 600)
        if self.settings.get('debug'):
            if is_fresh:
                console_write('Cached repsonse for "%s" is fresh (%ds).', (url, age))
            else:
                console_write('Cached repsonse for "%s" is %ds old, needs validation.', (url, age))
        return is_fresh

    def add_conditional_headers(self, url, headers):
        """
        Add `If-Modified-Since` and `If-None-Match` headers to a request if a
        cached copy exists

        :param headers:
            A dict with the request headers

        :return:
            The request headers dict, possibly with new headers added
        """
        cache = self.settings.get('cache')
        if not cache:
            return headers

        info_key = self.generate_key(url, '.info')
        info_json = cache.get(info_key)
        if not info_json:
            return headers

        # Make sure we have the cached content to use if we get a 304
        key = self.generate_key(url)
        if not cache.has(key):
            return headers

        try:
            info = json.loads(info_json.decode('utf-8'))
        except ValueError:
            return headers

        etag = info.get('etag')
        if etag:
            headers['If-None-Match'] = etag

        last_modified = info.get('last-modified')
        if last_modified:
            headers['If-Modified-Since'] = last_modified

        return headers

    def cache_result(self, method, url, status, headers, content):
        """
        Processes a request result, either caching the result, or returning
        the cached version of the url.

        :param method:
            The HTTP method used for the request

        :param url:
            The url of the request

        :param status:
            The numeric response status of the request

        :param headers:
            A dict of reponse headers, with keys being lowercase

        :param content:
            The response content

        :return:
            The response content
        """

        debug = self.settings.get('debug', False)
        cache = self.settings.get('cache')

        if not cache:
            if debug:
                console_write(
                    '''
                    Skipping cache since there is no cache object
                    '''
                )
            return content

        if method.lower() != 'get':
            if debug:
                console_write(
                    '''
                    Skipping cache since the HTTP method != GET
                    '''
                )
            return content

        status = int(status)

        # Don't do anything unless it was successful or not modified
        if status not in (200, 304):
            if debug:
                console_write(
                    '''
                    Skipping cache since the HTTP status code not one of: 200, 304
                    '''
                )
            return content

        key = self.generate_key(url)

        if status == 304:
            cached_content = cache.get(key)
            if cached_content:
                if debug:
                    console_write(
                        '''
                        Using cached content for %s from %s
                        ''',
                        (url, cache.path(key))
                    )
                cache.touch(key)
                return cached_content

            # If we got a 304, but did not have the cached content
            # stop here so we don't cache an empty response
            return content

        # If we got here, the status is 200

        # Respect some basic cache control headers
        cache_control = headers.get('cache-control', '')
        if cache_control:
            fields = re.split(r'\s*,\s*', cache_control)
            for field in fields:
                if field == 'no-store':
                    return content

        # Don't ever cache zip/binary files for the sake of hard drive space
        if headers.get('content-type') in ('application/zip', 'application/octet-stream'):
            if debug:
                console_write(
                    '''
                    Skipping cache since the response is a zip file
                    '''
                )
            return content

        etag = headers.get('etag')
        last_modified = headers.get('last-modified')

        if not etag and not last_modified:
            return content

        struct = {'etag': etag, 'last-modified': last_modified}
        struct_json = json.dumps(struct, indent=4)

        info_key = self.generate_key(url, '.info')
        if debug:
            console_write(
                '''
                Caching %s in %s
                ''',
                (url, cache.path(key))
            )

        cache.set(info_key, struct_json.encode('utf-8'))
        cache.set(key, content)

        return content

    def generate_key(self, url, suffix=''):
        """
        Generates a key to store the cache under

        :param url:
            The URL being cached

        :param suffix:
            A string to append to the key

        :return:
            A string key for the URL
        """

        if isinstance(url, str):
            url = url.encode('utf-8')

        key = hashlib.md5(url).hexdigest()
        return key + suffix

    def retrieve_cached(self, url):
        """
        Tries to return the cached content for a URL

        :param url:
            The URL to get the cached content for

        :return:
            The cached content
        """

        debug = self.settings.get('debug')
        cache = self.settings.get('cache')

        if not cache:
            if debug:
                console_write(
                    '''
                    Skipping cache since there is no cache object
                    '''
                )
            return False

        key = self.generate_key(url)

        cached_content = cache.get(key)
        if cached_content and debug:
            console_write(
                '''
                Using cached content for %s from %s
                ''',
                (url, cache.path(key))
            )

        return cached_content
