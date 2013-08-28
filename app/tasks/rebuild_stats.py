from ..lib.connection import connection


with connection() as cursor:
    cursor.execute("""
        TRUNCATE unique_package_installs;
        TRUNCATE daily_install_counts;
        TRUNCATE install_counts;

        INSERT INTO unique_package_installs (
            ip,
            package,
            sublime_platform
        )
        SELECT
            DISTINCT
            ip,
            package,
            sublime_platform
        FROM
            usage
        WHERE
            operation = 'install';

        INSERT INTO daily_install_counts (
            installs,
            osx_installs,
            linux_installs,
            windows_installs,
            date,
            package
        )
        SELECT
            COUNT(*) AS installs,
            SUM(CASE WHEN sublime_platform = 'osx' THEN 1 ELSE 0 END) AS osx_installs,
            SUM(CASE WHEN sublime_platform = 'linux' THEN 1 ELSE 0 END) AS linux_installs,
            SUM(CASE WHEN sublime_platform = 'windows' THEN 1 ELSE 0 END) AS windows_installs,
            DATE_TRUNC('day', date_time) AS date,
            package
        FROM
            usage
        WHERE
            operation = 'install'
        GROUP BY
            DATE_TRUNC('day', date_time),
            package;

        INSERT INTO install_counts (
            installs,
            osx_installs,
            linux_installs,
            windows_installs,
            package
        )
        SELECT
            SUM(installs) AS installs,
            SUM(osx_installs) AS osx_installs,
            SUM(linux_installs) AS linux_installs,
            SUM(windows_installs) AS windows_installs,
            package
        FROM
            daily_install_counts
        GROUP BY
            package;

        UPDATE install_counts
        SET
            unique_installs = sq.unique_installs,
            osx_unique_installs = sq.osx_unique_installs,
            linux_unique_installs = sq.linux_unique_installs,
            windows_unique_installs = sq.windows_unique_installs
        FROM
            (SELECT
                COUNT(*) AS unique_installs,
                SUM(CASE WHEN sublime_platform = 'osx' THEN 1 ELSE 0 END) AS osx_unique_installs,
                SUM(CASE WHEN sublime_platform = 'linux' THEN 1 ELSE 0 END) AS linux_unique_installs,
                SUM(CASE WHEN sublime_platform = 'windows' THEN 1 ELSE 0 END) AS windows_unique_installs,
                package
            FROM
                unique_package_installs
            GROUP BY
                package) AS sq
        WHERE
            sq.package = install_counts.package;
    """)
