from datetime import datetime

import psycopg2

from ...lib.connection import connection


def record(details):
    """
    Records that a user installed, upgraded or uninstalled a package
    """

    now = datetime.utcnow()
    today = now.date()

    package = details['package']
    ip = details['ip']
    platform = details['platform']
    operation = details['operation']

    if platform not in ['osx', 'linux', 'windows']:
        raise ValueError('Invalid platform')

    if operation not in ['install', 'upgrade', 'remove']:
        raise ValueError('Invalid operation')

    with connection() as cursor:
        # Record the unique user
        try:
            cursor.execute("""
                SAVEPOINT pre_ips;
                INSERT INTO ips (
                    ip,
                    sublime_platform
                )
                SELECT
                    %s,
                    %s
                WHERE
                    NOT EXISTS (
                        SELECT
                            1
                        FROM
                            ips
                        WHERE
                            ip = %s AND
                            sublime_platform = %s
                    );
                RELEASE pre_ips;
            """, [ip, platform, ip, platform])
        except (psycopg2.IntegrityError) as e:
            # Another request happened between the select and insert
            cursor.execute("ROLLBACK TO pre_ips")

        cursor.execute("""
            INSERT INTO usage (
                ip,
                user_agent,
                package,
                operation,
                date_time,
                version,
                old_version,
                package_control_version,
                sublime_platform,
                sublime_version
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, [
            ip,
            details['user_agent'],
            package,
            operation,
            now,
            details['version'],
            details['old_version'],
            details['package_control_version'],
            platform,
            details['sublime_version']
        ])

        if operation == 'install':
            # Record a unique package install
            increase_unique_installs = False
            try:
                cursor.execute("""
                    SAVEPOINT pre_unique_installs;
                    INSERT INTO unique_package_installs (
                        ip,
                        package,
                        sublime_platform
                    )
                    SELECT
                        %s,
                        %s,
                        %s
                    WHERE
                        NOT EXISTS (
                            SELECT
                                1
                            FROM
                                unique_package_installs
                            WHERE
                                ip = %s AND
                                package = %s AND
                                sublime_platform = %s
                        );
                    RELEASE pre_unique_installs;
                """, [ip, package, platform, ip, package, platform])
                if cursor.rowcount > 0:
                    increase_unique_installs = True
            except (psycopg2.IntegrityError) as e:
                # Another request happened between the select and insert
                cursor.execute("ROLLBACK TO pre_unique_installs")

            # Initialize the daily package stats if necessary
            try:
                cursor.execute("""
                    SAVEPOINT pre_daily_install_counts;
                    INSERT INTO daily_install_counts (
                        date,
                        package
                    )
                    SELECT
                        %s,
                        %s
                    WHERE
                        NOT EXISTS (
                            SELECT
                                1
                            FROM
                                daily_install_counts
                            WHERE
                                date = %s AND
                                package = %s
                        );
                    RELEASE pre_daily_install_counts;
                """, [today, package, today, package])
            except (psycopg2.IntegrityError) as e:
                # Another request happened between the select and insert
                cursor.execute("ROLLBACK TO pre_daily_install_counts")

            # Initialize the package stats if necessary
            try:
                cursor.execute("""
                    SAVEPOINT pre_install_counts;
                    INSERT INTO install_counts (
                        package
                    )
                    SELECT
                        %s
                    WHERE
                        NOT EXISTS (
                            SELECT
                                1
                            FROM
                                install_counts
                            WHERE
                                package = %s
                        );
                    RELEASE pre_install_counts;
                """, [package, package])
            except (psycopg2.IntegrityError) as e:
                # Another request happened between the select and insert
                cursor.execute("ROLLBACK TO pre_install_counts")

            # Update the various install counts
            if increase_unique_installs:
                cursor.execute("""
                    UPDATE
                        install_counts
                    SET
                        unique_installs = unique_installs + 1,
                        """ + platform + """_unique_installs = """ + platform + """_unique_installs + 1
                    WHERE
                        package = %s
                """, [package])

            cursor.execute("""
                UPDATE
                    install_counts
                SET
                    installs = installs + 1,
                    """ + platform + """_installs = """ + platform + """_installs + 1
                WHERE
                    package = %s
            """, [package])

            cursor.execute("""
                UPDATE
                    daily_install_counts
                SET
                    installs = installs + 1,
                    """ + platform + """_installs = """ + platform + """_installs + 1
                WHERE
                    package = %s AND
                    date = %s
            """, [package, today])
