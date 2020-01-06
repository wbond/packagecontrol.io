from ..lib.connection import connection


def begin():
    """
    Begins a new transaction - useful with update()
    """
    with connection(False) as cursor:
        cursor.execute('BEGIN')


def commit():
    """
    Commits a transaction opened with begin()
    """

    with connection(False) as cursor:
        cursor.execute('COMMIT')


def finished_parsing_log_file(filename):
    """
    Records parsing a log file

    :param filename:
        The log filename
    """

    with connection(False) as cursor:
        cursor.execute("""
            INSERT INTO parsed_log_files (
                filename
            ) VALUES (
                %s
            )
        """, [filename])


def log_file_previously_parsed(filename):
    """
    Checks if a log file was previously parsed

    :param filename:
        The log filename to check
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                filename
            FROM
                parsed_log_files
            WHERE
                filename = %s
        """, [filename])
        return cursor.rowcount > 0


def update(name, date, value):
    """
    Create or updates a system stat

    :param name:
        A stat to record

    :param date:
        A string 'YYYY-MM-DD' of the date to store the stats for

    :param value:
        A decimal with the value of the stat
    """

    with connection(False) as cursor:
        cursor.execute("""
            SELECT
                value
            FROM
                system_stats
            WHERE
                name = %s AND
                date = %s
        """, [name, date])
        if cursor.rowcount > 0:
            sql = """
                UPDATE
                    system_stats
                SET
                    value = value + %s
                WHERE
                    name = %s AND
                    date = %s
            """
        else:
            sql = """
                INSERT INTO system_stats (
                    value,
                    name,
                    date
                ) VALUES (
                    %s,
                    %s,
                    %s
                )
            """
        cursor.execute(sql, [value, name, date])


def fetch(interval='1 day'):
    """
    Fetches all of the system stats for the day specified by the interval

    :param interval:
        A text description of how many days ago to fetch the system stats for

    :return:
        A dict of {stat_name: value}
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                name,
                value
            FROM
                system_stats
            WHERE
                date = CURRENT_DATE - INTERVAL %s
        """, [interval])

        output = {}
        for row in cursor:
            output[row['name']] = row['value']

    return output


def gather_for(interval='1 day'):
    """
    Runs a bunch of queries to store statistics from the database

    :param interval:
        A text description of how many days ago to gather the system stats for
    """

    # Total downloads per day chart
    # Average number of packages per user
    with connection() as cursor:
        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'total_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'total_authors',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                (
                    SELECT
                        DISTINCT unnest(authors)
                    FROM
                        packages
                ) AS sq
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'total_users',
                CURRENT_DATE - INTERVAL %s,
                unique_installs
            FROM
                install_counts
            WHERE
                package = 'Package Control'
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'windows_users',
                CURRENT_DATE - INTERVAL %s,
                windows_unique_installs
            FROM
                install_counts
            WHERE
                package = 'Package Control'
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'osx_users',
                CURRENT_DATE - INTERVAL %s,
                osx_unique_installs
            FROM
                install_counts
            WHERE
                package = 'Package Control'
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'linux_users',
                CURRENT_DATE - INTERVAL %s,
                linux_unique_installs
            FROM
                install_counts
            WHERE
                package = 'Package Control'
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'st*_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                st_versions = ARRAY[2, 3, 4]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'st2_st3_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                st_versions = ARRAY[2, 3]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'st2_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                st_versions = ARRAY[2]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'st3_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                st_versions = ARRAY[3]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'st4_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                st_versions = ARRAY[4]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'windows_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                platforms @> ARRAY['windows']::varchar[]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'osx_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                platforms @> ARRAY['osx']::varchar[]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'linux_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                platforms @> ARRAY['linux']::varchar[]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'windows_osx_linux_packages',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                packages
            WHERE
                platforms @> ARRAY['osx', 'windows', 'linux']::varchar[]
        """, [interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'installs',
                CURRENT_DATE - INTERVAL %s,
                SUM(installs)
            FROM
                daily_install_counts
            WHERE
                date = CURRENT_DATE - INTERVAL %s
        """, [interval, interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'osx_installs',
                CURRENT_DATE - INTERVAL %s,
                SUM(osx_installs)
            FROM
                daily_install_counts
            WHERE
                date = CURRENT_DATE - INTERVAL %s
        """, [interval, interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'windows_installs',
                CURRENT_DATE - INTERVAL %s,
                SUM(windows_installs)
            FROM
                daily_install_counts
            WHERE
                date = CURRENT_DATE - INTERVAL %s
        """, [interval, interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'linux_installs',
                CURRENT_DATE - INTERVAL %s,
                SUM(linux_installs)
            FROM
                daily_install_counts
            WHERE
                date = CURRENT_DATE - INTERVAL %s
        """, [interval, interval])

        cursor.execute("""
            INSERT INTO system_stats (
                name,
                date,
                value
            )
            SELECT
                'total_labels',
                CURRENT_DATE - INTERVAL %s,
                COUNT(*)
            FROM
                (
                    SELECT
                        DISTINCT unnest(labels) AS label
                    FROM
                        packages
                ) AS sq
        """, [interval])


