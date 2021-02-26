import re
from datetime import datetime, timedelta

from ..lib.connection import connection


def all(limit_one_per_dependency=False):
    """
    Fetches info about all dependencies for the purpose of writing JSON files

    :return:
        A dict in the form:
        {
            'Dependency Name': {
                'name': 'Package Name',
                'load_order': '01',
                'authors': ['author', 'names'],
                'description': 'Package description',
                'issues': 'http://example.com/issues',
                'releases': [
                    {
                        'version': '1.0.0',
                        'url': 'https://example.com/download',
                        'sublime_text': '*',
                        'platforms': ['*']
                    }
                ]
            }
        }
    """

    output = {}
    with connection() as cursor:
        cursor.execute("""
            SELECT
                sources[1] AS repository,
                name,
                load_order,
                authors,
                description,
                issues
            FROM
                dependencies
            WHERE
                is_missing != TRUE AND
                removed != TRUE AND
                needs_review != TRUE
            ORDER BY
                repository ASC,
                LOWER(name) ASC
        """)
        for row in cursor.fetchall():
            output[row['name']] = {
                'repository':     row['repository'],
                'name':           row['name'],
                'load_order':     row['load_order'],
                'authors':        row['authors'],
                'description':    row['description'],
                'issues':         row['issues'],
                'releases':       []
            }

        cursor.execute("""
            SELECT
                dr.dependency,
                dr.platforms,
                dr.sublime_text,
                dr.version,
                dr.url,
                dr.sha256,
                CASE
                    WHEN dr.version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+-'
                        then -1
                    WHEN dr.version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\+'
                        then 1
                    ELSE 0
                END AS semver_variant
            FROM
                dependency_releases AS dr INNER JOIN
                dependencies AS d ON dr.dependency = d.name
            WHERE
                d.is_missing != TRUE AND
                d.removed != TRUE AND
                d.needs_review != TRUE
            ORDER BY
                d.sources[1:1] ASC,
                LOWER(d.name) ASC,
                -- The semver without a suffix
                string_to_array(regexp_replace(version, E'^(\\\\d+\\\\.\\\\d+\\\\.\\\\d+)[^\\\\d].*$', E'\\\\1'), '.')::int[] DESC,
                -- If the version is a build, bare or prerelease
                CASE
                    WHEN version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+-'
                        then -1
                    WHEN version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\+'
                        then 1
                    ELSE 0
                END DESC,
                -- Perform the version munging that PC does for date-based versions
                CASE
                    WHEN version ~ E'^\\\\d{4}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}$'
                        THEN '0.' || version
                    ELSE version
                END DESC
        """)

        dependencies_found = {}

        for row in cursor.fetchall():
            dependency = row['dependency']
            # Skip pre-releases for dependencies
            if row['semver_variant'] == -1:
                continue

            key = '%s-%s-%s' % (dependency, row['sublime_text'], ','.join(row['platforms']))
            if limit_one_per_dependency:
                if key in dependencies_found:
                    continue

            release = {
                'platforms':    row['platforms'],
                'sublime_text': row['sublime_text'],
                'version':      row['version'],
                'url':          row['url']
            }
            if row['sha256']:
                release['sha256'] = row['sha256']

            output[dependency]['releases'].append(release)

            if limit_one_per_dependency:
                dependencies_found[key] = True

    return output


def dependent_sources(source):
    """
    Fetches a list of sources needed to fully refresh all dependencies from the specified source

    :param source:
        The string source (URL) to find the dependencies of

    :return:
        A list of sources (URLs) for dependencies to be refreshed
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                dependencies
            WHERE
                sources @> ARRAY[%s]::varchar[]
        """, [source])
        return [row['source'] for row in cursor]


def outdated_sources(minutes, limit):
    """
    Fetches a list of outdated dependency sources in the DB

    :param minutes:
        The int number of minutes to be considered "outdated"

    :return:
        A list of sources (URLs) for dependencies that need to be refreshed
    """

    outdated_date = datetime.utcnow() - timedelta(minutes=minutes)

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                (
                    SELECT
                        sources
                    FROM
                        dependencies
                    WHERE
                        last_seen <= %s
                    ORDER BY
                        last_seen ASC
                    LIMIT
                        %s
                ) AS sq
        """, [outdated_date, limit])
        return [row['source'] for row in cursor]


def invalid_sources(valid_sources):
    """
    Fetches a list of all other known sources

    :param valid_sources:
        The list of sources that are valid

    :return:
        A list of sources (URLs) for dependencies that should be ignored
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                dependencies
        """)
        all_sources = [row['source'] for row in cursor]

    return [source for source in all_sources if source not in valid_sources]


def old():
    """
    Finds all dependencies that haven't been seen in at least two hours

    :return:
        A list of dict objects containing the keys:
         - name
         - sources
         - is_missing
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                name,
                sources,
                is_missing
            FROM
                dependencies
            WHERE
                last_seen < CURRENT_TIMESTAMP - INTERVAL '2 hours' AND
                removed != TRUE AND
                needs_review != TRUE
        """)

        return cursor.fetchall()


def mark_found(dependencies):
    """
    Marks a dependencies as no longer missing

    :param dependencies:
        The name of the dependencies
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                dependencies
            SET
                is_missing = FALSE,
                missing_error = '',
                removed = FALSE
            WHERE
                name = %s
        """, [dependencies])


def mark_missing(source, error):
    """
    Marks all dependencies from a source as currently missing

    :param source:
        The URL of the source that could not be contacted
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                dependencies
            SET
                is_missing = TRUE,
                missing_error = %s,
                needs_review = TRUE
            WHERE
                sources @> ARRAY[%s]::varchar[]
        """, [error, source])


def mark_missing_by_name(dependency, error):
    """
    Marks a dependency as missing

    :param dependency:
        The name of the dependency
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                dependencies
            SET
                is_missing = TRUE,
                missing_error = %s,
                needs_review = TRUE
            WHERE
                name = %s
        """, [error, dependency])


def mark_removed(dependency):
    """
    Marks a dependency as removed

    :param dependency:
        The name of the dependency
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                dependencies
            SET
                removed = TRUE,
                is_missing = FALSE,
                missing_error = '',
                needs_review = TRUE
            WHERE
                name = %s
        """, [dependency])


def store(values):
    """
    Stores dependency info in the database

    :param values:
        A dict containing the following keys:
          `name`
          `load_order`
          `author`
          `description`
          `issues`
          `sources`
          `releases`
    """

    name = values['name']

    with connection() as cursor:
        cursor.execute("SELECT name FROM dependencies WHERE name = %s", [name])

        if cursor.fetchone() == None:
            sql = """
                INSERT INTO dependencies (
                    load_order,
                    authors,
                    description,
                    issues,
                    last_seen,
                    sources,
                    name
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    %s,
                    %s
                )
            """
        else:
            sql = """
                UPDATE
                    dependencies
                SET
                    load_order = %s,
                    authors = %s,
                    description = %s,
                    issues = %s,
                    last_seen = CURRENT_TIMESTAMP,
                    sources = %s
                WHERE
                    name = %s
            """

        if not isinstance(values['author'], list):
            authors = re.split('\s*,\s*', values['author'])
        else:
            authors = values['author']

        cursor.execute(sql, [
            values['load_order'],
            authors,
            values['description'],
            values['issues'],
            values['sources'],
            name
        ])

        cursor.execute("DELETE FROM dependency_releases WHERE dependency = %s", [name])

        for release in values['releases']:
            sql = """
                INSERT INTO dependency_releases (
                    dependency,
                    platforms,
                    sublime_text,
                    version,
                    url,
                    sha256
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
                release.get('sha256')
            ])
