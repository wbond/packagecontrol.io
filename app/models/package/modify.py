import re

from ...lib.connection import connection


def cleanup_renames():
    """
    Looks through all renamed packages and makes sure all stats for previous
    name are applied to the current name. Only peforms one rename per
    invocation since the renames hit the DB quite a bit.

    :return:
        A dict of {old_name: new_name}
    """

    output = {}
    with connection() as cursor:
        cursor.execute("""
            SELECT
                name,
                previous_names
            FROM
                packages
            WHERE
                previous_names <> ARRAY[]::varchar[]
        """)
        for row in cursor.fetchall():
            name = row['name']
            previous_names = row['previous_names']

            for prev_name in previous_names:
                cursor.execute("""
                    SELECT
                        name
                    FROM
                        packages
                    WHERE
                        name = %s
                """, [prev_name])

                if not cursor.rowcount:
                    continue

                print('Processing %s -> %s' % (prev_name, name))
                output[prev_name] = name

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
                if cursor.rowcount:
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

                # Any remaining unique installs for the old package are
                # duplicates of unique installs for the new package, so we
                # can just delete them
                cursor.execute("""
                    DELETE FROM
                        unique_package_installs
                    WHERE
                        package = %s
                """, [prev_name])

                # We do NOT update the usage table since we want that to be
                # a historical record of what actually happened. This also
                # allows us to reconstruct corrupted data.

                # Clean up the old package entry
                cursor.execute("""
                    DELETE FROM
                        packages
                    WHERE
                        name = %s
                """, [prev_name])

            # Break after a single rename since they can take quite a
            # while and we don't want to lock up the DB in the process
            if len(output.keys()) > 0:
                break

    return output


def delete_readme(package):
    """
    Deletes a package readme from the database

    :param package:
        The name of the package to delete the readme for
    """

    with connection() as cursor:
        cursor.execute("DELETE FROM readmes WHERE package = %s", [package])


def mark_found(package):
    """
    Marks a package as no longer missing

    :param package:
        The name of the package
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                package_stats
            SET
                is_missing = FALSE,
                missing_error = '',
                removed = FALSE
            WHERE
                package = %s
        """, [package])


def mark_missing(source, error):
    """
    Marks all packages from a source as currently missing

    :param source:
        The URL of the source that could not be contacted
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                package_stats
            SET
                is_missing = TRUE,
                missing_error = %s
            FROM
                packages AS p
            WHERE
                p.name = package_stats.package AND
                p.sources @> ARRAY[%s]::varchar[]
        """, [error, source])


def mark_missing_by_name(package, error):
    """
    Marks a package as missing

    :param package:
        The name of the package
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                package_stats
            SET
                is_missing = TRUE,
                missing_error = %s
            WHERE
                package = %s
        """, [error, package])


def mark_removed(package):
    """
    Marks a package as removed

    :param package:
        The name of the package
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                package_stats
            SET
                removed = TRUE,
                is_missing = FALSE,
                missing_error = ''
            WHERE
                package = %s
        """, [package])


def store(values):
    """
    Stores package info in the database

    :param values:
        A dict containing the following keys:
          `name`
          `description`
          `author`
          `homepage`
          `releases`
          `previous_names`
          `labels`
          `last_modified`
          `sources`
          `readme`
          `issues`
          `donate`
          `buy`
    """

    name = values['name']

    with connection() as cursor:
        cursor.execute("SELECT name FROM packages WHERE name = %s", [name])

        if cursor.fetchone() == None:
            sql = """
                INSERT INTO packages (
                    description,
                    author,
                    homepage,
                    previous_names,
                    labels,
                    platforms,
                    st_versions,
                    last_modified,
                    last_seen,
                    sources,
                    readme,
                    issues,
                    donate,
                    buy,
                    name
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """
        else:
            sql = """
                UPDATE
                    packages
                SET
                    description = %s,
                    author = %s,
                    homepage = %s,
                    previous_names = %s,
                    labels = %s,
                    platforms = %s,
                    st_versions = %s,
                    last_modified = %s,
                    last_seen = CURRENT_TIMESTAMP,
                    sources = %s,
                    readme = %s,
                    issues = %s,
                    donate = %s,
                    buy = %s
                WHERE
                    name = %s
            """

        platforms = []
        st_versions = []

        for release in values['releases']:
            if '*' in release['platforms']:
                platforms = ['windows', 'osx', 'linux']
            else:
                for platform in release['platforms']:
                    platform = re.sub('-x(32|64)$', '', platform)
                    if platform not in platforms:
                        platforms.append(platform)

            st = release['sublime_text']
            if st == '>2999' or st[0:2] == '>3' or st[0:3] == '>=3':
                if 3 not in st_versions:
                    st_versions.append(3)
            elif st == '<3000' or st[0:2] == '<2' or st[0:3] == '<=2':
                if 2 not in st_versions:
                    st_versions.append(2)
            else:
                st_versions = [2,3]

        cursor.execute(sql, [
            values['description'],
            values['author'],
            values['homepage'],
            values['previous_names'],
            values['labels'],
            platforms,
            st_versions,
            values['last_modified'],
            values['sources'],
            values['readme'],
            values['issues'],
            values['donate'],
            values['buy'],
            name
        ])

        cursor.execute("DELETE FROM releases WHERE package = %s", [name])

        for release in values['releases']:
            sql = """
                INSERT INTO releases (
                    package,
                    platforms,
                    sublime_text,
                    version,
                    url,
                    date
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            # Do some consistency fixes for the sake of simplifying some SQL
            # later on when selecting unique version info
            sublime_text = release['sublime_text']
            fixes = {
                # Consistency
                '>2999':  '>=3000',
                '<=2999': '<3000',
                # Semantic mistakes
                '>3000':  '>=3000',
                '<=3000': '<3000'
            }
            if sublime_text in fixes:
                sublime_text = fixes[sublime_text]

            cursor.execute(sql, [
                name,
                release['platforms'],
                sublime_text,
                release['version'],
                release['url'],
                release['date']
            ])


def store_readme(values):
    """
    Stores a package readme in the database

    :param values:
        A dict containing the following keys:
          `package`
          `filename`
          `format`
          `source`
          `rendered_html`
    """

    package = values['package']

    with connection() as cursor:
        cursor.execute("SELECT package FROM readmes WHERE package = %s", [package])

        if cursor.fetchone() == None:
            sql = """
                INSERT INTO readmes (
                    filename,
                    format,
                    source,
                    rendered_html,
                    package
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """
        else:
            sql = """
                UPDATE
                    readmes
                SET
                    filename = %s,
                    format = %s,
                    source = %s,
                    rendered_html = %s
                WHERE
                    package = %s
            """

        cursor.execute(sql, [
            values['filename'],
            values['format'],
            values['source'],
            values['rendered_html'],
            package
        ])
