from ...lib.connection import connection


def refresh():
    """
    Recalculates the unique installs rank and trending stats about each package.
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                package_stats
            SET
                installs_rank = sq.rank
            FROM
                (
                    SELECT
                        p.name AS package,
                        row_number() OVER (ORDER BY ic.unique_installs DESC) AS rank
                    FROM
                        packages AS p INNER JOIN
                        install_counts AS ic ON p.name = ic.package
                    ORDER BY
                        ic.unique_installs DESC
                ) AS sq
            WHERE
                sq.package = package_stats.package
        """)

        cursor.execute("""
            UPDATE
                package_stats
            SET
                trending_rank = NULL,
                z_value = NULL;

            UPDATE
                package_stats
            SET
                trending_rank = sq.z_value_rank,
                z_value = sq.z_value
            FROM
                (
                    SELECT
                        package,
                        z_value,
                        row_number() OVER (ORDER BY z_value DESC) AS z_value_rank
                    FROM
                        (
                            SELECT
                                p.name AS package,
                                (t.installs - h.installs_mean) / (h.installs_stddev + 0.000001) AS z_value

                            FROM
                                packages AS p INNER JOIN
                                (
                                    SELECT
                                        package,
                                        avg(installs) AS installs_mean,
                                        stddev_pop(installs) AS installs_stddev
                                    FROM
                                        daily_install_counts
                                    WHERE
                                        date >= (CURRENT_DATE - interval '1 day' - interval '6 weeks')
                                    GROUP BY
                                        package
                                ) AS h ON p.name = h.package INNER JOIN

                                -- The two most recent full days of stats
                                (
                                    SELECT
                                        package,
                                        (SUM(installs) / 2) AS installs
                                    FROM
                                        daily_install_counts
                                    WHERE
                                        date = CURRENT_DATE - interval '1 day' OR
                                        date = CURRENT_DATE - interval '2 days'
                                    GROUP BY
                                        package

                                ) AS t ON p.name = t.package

                            WHERE
                                -- Make sure the packages have some users
                                t.installs > 10

                            ORDER BY
                                z_value DESC

                            LIMIT 100
                        ) AS z
                ) AS sq
            WHERE
                sq.package = package_stats.package
        """)
