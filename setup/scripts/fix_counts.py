#!/usr/bin/env python

from app.lib.connection import connection

results = []
with connection() as cursor:
    cursor.execute("""
        select
            name,
            previous_names
        from
            packages
        where
            previous_names != ARRAY[]::varchar[]
        order by
            name
    """)
    results = cursor.fetchall()

for result in results:
    name = result['name']
    print(name)

    for prev_name in result['previous_names']:
        print('  ' + prev_name)

        with connection(transaction=False) as cursor:
            cursor.execute('BEGIN')
            cursor.execute("""
                SELECT
                    *
                FROM
                    package_stats
                WHERE
                    package in (%s, %s)
                ORDER BY
                    CASE package
                        WHEN %s THEN 1
                        ELSE 2
                    END
            """, [prev_name, name, prev_name])

            # If there is no first install info, we already processed it
            if cursor.rowcount == 2:
                previous_stats = cursor.fetchone()
                current_stats = cursor.fetchone()

                def pick_first(val1, val2):
                    if not val2:
                        return val1
                    if not val1:
                        return val2
                    if val1 < val2:
                        return val1
                    return val2

                def pick_highest(val1, val2):
                    if not val2:
                        return val1
                    if not val1:
                        return val2
                    if val1 > val2:
                        return val1
                    return val2

                # Update the package stats with the best value from the
                # previous name and the current name
                cursor.execute("""
                    UPDATE
                        package_stats
                    SET
                        first_seen = %s,
                        installs_rank = %s,
                        trending_rank = %s,
                        z_value = %s
                    WHERE
                        package = %s
                """, [
                    pick_first(previous_stats['first_seen'], current_stats['first_seen']),
                    pick_first(previous_stats['installs_rank'], current_stats['installs_rank']),
                    pick_first(previous_stats['trending_rank'], current_stats['trending_rank']),
                    pick_highest(previous_stats['z_value'], current_stats['z_value']),
                    name
                ])

                if cursor.rowcount:
                    print('   - Updated package stats')

                cursor.execute("""
                    DELETE FROM
                        package_stats
                    WHERE
                        package = %s
                """, [prev_name])

            # Find all daily install counts where there is no version for
            # the new package name and just change the package name
            cursor.execute("""
                UPDATE
                    daily_install_counts
                SET
                    package = %s
                WHERE
                    package = %s AND
                    date NOT IN (
                        SELECT
                            date
                        FROM
                            daily_install_counts
                        WHERE
                            package = %s
                    )
            """, [name, prev_name, name])

            if cursor.rowcount:
                print('   - Moved daily install counts: %s' % cursor.rowcount)

            # Add all counts for the old name to the new name
            cursor.execute("""
                UPDATE
                    daily_install_counts AS d
                SET
                    installs         = d.installs         + d2.installs,
                    osx_installs     = d.osx_installs     + d2.osx_installs,
                    windows_installs = d.windows_installs + d2.windows_installs,
                    linux_installs   = d.linux_installs   + d2.linux_installs
                FROM
                    daily_install_counts AS d2
                WHERE
                    d.date = d2.date AND
                    d.package = %s AND
                    d2.package = %s
            """, [name, prev_name])

            if cursor.rowcount:
                print('   - Merged daily install counts: %s' % cursor.rowcount)

            # Remove the records we just added
            cursor.execute("""
                DELETE FROM
                    daily_install_counts
                WHERE
                    package = %s
            """, [prev_name])

            # Add a new install counts entry if it is missing
            cursor.execute("""
                SELECT
                    package
                FROM
                    install_counts
                WHERE
                    package = %s
            """, [name])
            if not cursor.rowcount:
                cursor.execute("""
                    INSERT INTO install_counts (
                        package
                    ) VALUES (
                        %s
                    )
                """, [name])
                print('   - Added install counts entry')

            # For the raw installs, we can just add the old package to the new
            cursor.execute("""
                UPDATE
                    install_counts AS ic
                SET
                    installs         = ic.installs         + ic2.installs,
                    osx_installs     = ic.osx_installs     + ic2.osx_installs,
                    windows_installs = ic.windows_installs + ic2.windows_installs,
                    linux_installs   = ic.linux_installs   + ic2.linux_installs
                FROM
                    install_counts AS ic2
                WHERE
                    ic.package = %s AND
                    ic2.package = %s
            """, [name, prev_name])

            if cursor.rowcount:
                print('   - Merged raw install counts')

            # Remove the install counts for the old package
            cursor.execute("""
                DELETE FROM
                    install_counts
                WHERE
                    package = %s
            """, [prev_name])

            # For unique installs, we need to count how many unique installs
            # we can move from the old name to the new name and add that many
            for platform in ['linux', 'windows', 'osx']:
                cursor.execute("""
                    UPDATE
                        unique_package_installs
                    SET
                        package = %s
                    WHERE
                        package = %s AND
                        sublime_platform = %s AND
                        ip NOT IN (
                            SELECT
                                ip
                            FROM
                                unique_package_installs
                            WHERE
                                package = %s AND
                                sublime_platform = %s
                        )
                """, [name, prev_name, platform, name, platform])
                affected = cursor.rowcount
                cursor.execute("""
                    UPDATE
                        install_counts
                    SET
                        """ + platform + """_unique_installs = """ + platform + """_unique_installs + %s,
                        unique_installs = unique_installs + %s
                    WHERE
                        package = %s
                """, [affected, affected, name])
                print('   - Added unique %s install counts: %s' % (platform, affected))

            # Any remaining unique installs for the old package are
            # duplicates of unique installs for the new package, so we
            # can just delete them
            cursor.execute("""
                DELETE FROM
                    unique_package_installs
                WHERE
                    package = %s
            """, [prev_name])

            cursor.execute('COMMIT')


