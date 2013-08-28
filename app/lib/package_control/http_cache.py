# Not shared with Package Control

from datetime import datetime, timedelta

from ..connection import connection


class HttpCache(object):
    """
    A data store for caching HTTP response data.
    """

    def __init__(self, ttl):
        self.clear(int(ttl))


    def clear(self, ttl):
        """
        Removes all cache entries older than the TTL

        :param ttl:
            The number of seconds a cache entry should be valid for
        """

        ttl = int(ttl)
        cutoff = datetime.utcnow() - timedelta(seconds=ttl)

        with connection() as cursor:
            cursor.execute("DELETE FROM http_cache_entries WHERE last_modified < %s", [cutoff])


    def get(self, key):
        """
        Returns a cached value

        :param key:
            The key to fetch the cache for

        :return:
            The (binary) cached value, or False
        """

        with connection() as cursor:
            cursor.execute("SELECT content FROM http_cache_entries WHERE key = %s", [key])
            row = cursor.fetchone()
            if not row:
                return False

            return row['content'].tobytes()


    def has(self, key):
        with connection() as cursor:
            cursor.execute("SELECT key FROM http_cache_entries WHERE key = %s", [key])
            return cursor.fetchone() != None


    def set(self, key, content):
        """
        Saves a value in the cache

        :param key:
            The key to save the cache with

        :param content:
            The (binary) content to cache
        """

        if self.has(key):
            sql = "UPDATE http_cache_entries SET content = %s, last_modified = CURRENT_TIMESTAMP WHERE key = %s"
        else:
            sql = "INSERT INTO http_cache_entries (content, last_modified, key) VALUES (%s, CURRENT_TIMESTAMP, %s)"

        with connection() as cursor:
            cursor.execute(sql, [content, key])
