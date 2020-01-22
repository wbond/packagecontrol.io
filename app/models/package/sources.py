from datetime import datetime, timedelta

from ...lib.connection import connection


def dependent_sources(source):
    """
    Fetches a list of sources needed to fully refresh all packages from the specified source

    :param source:
        The string source (URL) to find the dependencies of

    :return:
        A list of sources (URLs) for packages to be refreshed
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(p.sources) AS source
            FROM
                packages AS p
                INNER JOIN package_stats AS ps
                    ON p.name = ps.package
            WHERE
                p.sources @> ARRAY[%s]::varchar[] AND
                ps.removed != TRUE

        """, [source])
        return [row['source'] for row in cursor]


def outdated_sources(minutes, limit):
    """
    Fetches a list of outdated sources in the DB

    :param minutes:
        The int number of minutes to be considered "outdated"

    :return:
        A list of sources (URLs) for packages that need to be refreshed
    """

    outdated_date = datetime.utcnow() - timedelta(minutes=minutes)

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                (
                    SELECT
                        p.sources
                    FROM
                        packages AS p
                        INNER JOIN package_stats AS ps
                            ON p.name = ps.package
                    WHERE
                        p.last_seen <= %s AND
                        ps.removed != TRUE
                    ORDER BY
                        p.last_seen ASC
                    LIMIT
                        %s
                ) AS packages
        """, [outdated_date, limit])
        return [row['source'] for row in cursor]


def invalid_sources(valid_sources):
    """
    Fetches a list of all other known sources

    :param valid_sources:
        The list of sources that are valid

    :return:
        A list of sources (URLs) for packages that should be ignored
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                packages AS p
                INNER JOIN package_stats AS ps
                    ON p.name = ps.package
            WHERE
                ps.removed != TRUE
        """)
        all_sources = [row['source'] for row in cursor]

    return [source for source in all_sources if source not in valid_sources]


def sources_for(package):
    """
    Fetches a list of sources needed to refresh a package

    :param package:
        A unicode string of the package name to refresh

    :return:
        A list of sources (URLs) for the package
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                packages
            WHERE
                name = %s
        """, [package])
        return [row['source'] for row in cursor]
