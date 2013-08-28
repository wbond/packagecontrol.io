from threading import Lock
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from .. import config


@contextmanager
def connection(transaction=True):
    connection = _grab()

    try:
        cursor = connection.cursor()
        yield cursor

    except Exception:
        # Make sure the connection is in a clean state
        connection.rollback()
        raise

    else:
        # Save the changes from this block
        if transaction:
            connection.commit()

    finally:
        cursor.close()
        _release(connection)


# A list of psycopg2 connection objects
_connections = []

# Make sure connection management doesn't run into threading issues
_lock = Lock()


def _grab():
    global _connections, _lock

    _lock.acquire()
    try:
        if not _connections:
            _connections.append(_create_connection())

        return _connections.pop()
    finally:
        _lock.release()


def _release(connection):
    global _connections, _lock

    _lock.acquire()
    try:
        _connections.append(connection)
    finally:
        _lock.release()


def _create_connection():
    """
    Connects to a database and returns the connection object

    :return:
        A psycopg2 connection object
    """

    params = config.read('db', True)
    connection_params = {
        'database': params['database'],
        'user': params['user'],
        'password': params.get('password'),
        'host': params['host'],
        'connection_factory': psycopg2.extras.RealDictConnection
    }
    _connection = psycopg2.connect(**connection_params)
    _connection.cursor().execute("SET TIMEZONE = 'UTC'")

    return _connection
