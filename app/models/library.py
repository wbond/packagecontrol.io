import re
from datetime import datetime, timedelta

from ..lib.connection import connection


def all(limit_one_per_library=False):
    """
    Fetches info about all libraries for the purpose of writing JSON files

    :return:
        A dict in the form:
        {
            'Library Name': {
                'name': 'Package Name',
                'authors': ['author', 'names'],
                'description': 'Package description',
                'issues': 'http://example.com/issues',
                'releases': [
                    {
                        'version': '1.0.0',
                        'url': 'https://example.com/download',
                        'sublime_text': '*',
                        'platforms': ['*'],
                        'python_versions': ['3.3', '3.8']
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
                authors,
                description,
                issues
            FROM
                libraries
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
                'authors':        row['authors'],
                'description':    row['description'],
                'issues':         row['issues'],
                'releases':       []
            }

        cursor.execute("""
            SELECT
                dr.library,
                dr.platforms,
                dr.python_versions,
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
                library_releases AS dr INNER JOIN
                libraries AS d ON dr.library = d.name
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

        libraries_found = {}

        for row in cursor.fetchall():
            library = row['library']
            # Skip pre-releases for libraries
            if row['semver_variant'] == -1:
                continue

            key = '%s-%s-%s' % (library, row['sublime_text'], ','.join(row['platforms']))
            if limit_one_per_library:
                if key in libraries_found:
                    continue

            release = {
                'platforms':       row['platforms'],
                'python_versions': row['python_versions'],
                'sublime_text':    row['sublime_text'],
                'version':         row['version'],
                'url':             row['url']
            }
            if row['sha256']:
                release['sha256'] = row['sha256']

            output[library]['releases'].append(release)

            if limit_one_per_library:
                libraries_found[key] = True

    return output


def dependent_sources(source):
    """
    Fetches a list of sources needed to fully refresh all libraries from the specified source

    :param source:
        The string source (URL) to find the libraries of

    :return:
        A list of sources (URLs) for libraries to be refreshed
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                libraries
            WHERE
                sources @> ARRAY[%s]::varchar[]
        """, [source])
        return [row['source'] for row in cursor]


def outdated_sources(minutes, limit):
    """
    Fetches a list of outdated library sources in the DB

    :param minutes:
        The int number of minutes to be considered "outdated"

    :return:
        A list of sources (URLs) for libraries that need to be refreshed
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
                        libraries
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
        A list of sources (URLs) for libraries that should be ignored
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                DISTINCT unnest(sources) AS source
            FROM
                libraries
        """)
        all_sources = [row['source'] for row in cursor]

    return [source for source in all_sources if source not in valid_sources]


def old():
    """
    Finds all libraries that haven't been seen in at least two hours

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
                libraries
            WHERE
                last_seen < CURRENT_TIMESTAMP - INTERVAL '2 hours' AND
                removed != TRUE AND
                needs_review != TRUE
        """)

        return cursor.fetchall()


def mark_found(libraries):
    """
    Marks a libraries as no longer missing

    :param libraries:
        The name of the libraries
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                libraries
            SET
                is_missing = FALSE,
                missing_error = '',
                removed = FALSE
            WHERE
                name = %s
        """, [libraries])


def mark_missing(source, error, needs_review):
    """
    Marks all libraries from a source as currently missing

    :param source:
        The URL of the source that could not be contacted

    :param error:
        A unicode string of the error

    :param needs_review:
        A bool if the library needs to be reviewed
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                libraries
            SET
                is_missing = TRUE,
                missing_error = %s,
                needs_review = %s
            WHERE
                sources @> ARRAY[%s]::varchar[]
        """, [error, needs_review, source])


def mark_missing_by_name(library, error, needs_review):
    """
    Marks a library as missing

    :param library:
        The name of the library

    :param error:
        A unicode string of the error

    :param needs_review:
        A bool if the library needs to be reviewed
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                libraries
            SET
                is_missing = TRUE,
                missing_error = %s,
                needs_review = %s
            WHERE
                name = %s
        """, [error, needs_review, library])


def mark_removed(library):
    """
    Marks a library as removed

    :param library:
        The name of the library
    """

    with connection() as cursor:
        cursor.execute("""
            UPDATE
                libraries
            SET
                removed = TRUE,
                is_missing = FALSE,
                missing_error = '',
                needs_review = TRUE
            WHERE
                name = %s
        """, [library])


def store(values):
    """
    Stores library info in the database

    :param values:
        A dict containing the following keys:
          `name`
          `author`
          `description`
          `issues`
          `sources`
          `releases`
    """

    name = values['name']

    with connection() as cursor:
        cursor.execute("SELECT name FROM libraries WHERE name = %s", [name])

        if cursor.fetchone() == None:
            sql = """
                INSERT INTO libraries (
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
                    CURRENT_TIMESTAMP,
                    %s,
                    %s
                )
            """
        else:
            sql = """
                UPDATE
                    libraries
                SET
                    authors = %s,
                    description = %s,
                    issues = %s,
                    last_seen = CURRENT_TIMESTAMP,
                    sources = %s
                WHERE
                    name = %s
            """

        if not isinstance(values['author'], list):
            authors = re.split(r'\s*,\s*', values['author'])
        else:
            authors = values['author']

        cursor.execute(sql, [
            authors,
            values['description'],
            values['issues'],
            values['sources'],
            name
        ])

        cursor.execute("DELETE FROM library_releases WHERE library = %s", [name])

        for release in values['releases']:
            sql = """
                INSERT INTO library_releases (
                    library,
                    platforms,
                    python_versions,
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
                release['python_versions'],
                sublime_text,
                release['version'],
                release['url'],
                release.get('sha256')
            ])
