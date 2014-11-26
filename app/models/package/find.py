import re
from datetime import datetime, timedelta

from ... import config
from ...lib.connection import connection
from ..not_found_error import NotFoundError
from ... import cache


synonyms = config.read('synonyms')


def all(limit_one_per_package=False):
    """
    Fetches info about all packages for the purpose of writing JSON files

    :return:
        A dict in the form:
        {
            'Package Name': {
                'name': 'Package Name',
                'description': 'Package description',
                'authors': ['author', 'names'],
                'homepage': 'http://example.com',
                'previous_names': [],
                'labels': ['color scheme'],
                'last_modified': '2013-07-31 08:41:20',
                'readme': 'http://example.com/readme',
                'issues': 'http://example.com/issues',
                'donate': 'http://example.com/donate',
                'buy': 'http://example.com/buy'
            }
        }
    """

    output = {}
    with connection() as cursor:
        cursor.execute("""
            SELECT
                p.sources[1] AS repository,
                p.name,
                p.description,
                p.authors,
                p.homepage,
                p.previous_names,
                p.labels,
                p.last_modified,
                p.readme,
                p.issues,
                p.donate,
                p.buy
            FROM
                packages AS p
                INNER JOIN package_stats AS ps
                    ON p.name = ps.package
            WHERE
                ps.is_missing != TRUE AND
                ps.removed != TRUE
            ORDER BY
                repository ASC,
                LOWER(p.name) ASC
        """)
        for row in cursor.fetchall():
            output[row['name']] = {
                'repository':     row['repository'],
                'name':           row['name'],
                'description':    row['description'],
                'authors':        row['authors'],
                'homepage':       row['homepage'],
                'previous_names': row['previous_names'],
                'labels':         row['labels'],
                'last_modified':  row['last_modified'],
                'readme':         row['readme'],
                'issues':         row['issues'],
                'donate':         row['donate'],
                'buy':            row['buy'],
                'releases':       []
            }

        cursor.execute("""
            SELECT
                r.package,
                r.platforms,
                r.sublime_text,
                r.version,
                r.url,
                r.date,
                CASE
                    WHEN r.version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+-'
                        then -1
                    WHEN r.version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\+'
                        then 1
                    ELSE 0
                END AS semver_variant
            FROM
                releases AS r INNER JOIN
                packages AS p ON r.package = p.name INNER JOIN
                package_stats AS ps
                    ON p.name = ps.package
            WHERE
                ps.is_missing != TRUE AND
                ps.removed != TRUE
            ORDER BY
                p.sources[1:1] ASC,
                LOWER(p.name) ASC,
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

        packages_with_prerelease = {}
        packages_with_non_prerelease = {}

        for row in cursor.fetchall():
            package = row['package']
            prerelease = row['semver_variant'] == -1

            key = '%s-%s-%s' % (package, row['sublime_text'], ','.join(row['platforms']))
            if limit_one_per_package:
                if prerelease and key in packages_with_prerelease:
                    continue
                if not prerelease and key in packages_with_non_prerelease:
                    continue

            output[package]['releases'].append({
                'platforms':    row['platforms'],
                'sublime_text': row['sublime_text'],
                'version':      row['version'],
                'url':          row['url'],
                'date':         row['date']
            })

            if limit_one_per_package:
                if prerelease:
                    packages_with_prerelease[key] = True
                else:
                    packages_with_non_prerelease[key] = True

    return output


def old():
    """
    Finds all packages that haven't been seen in at least two hours

    :return:
        A list of dict objects containing the keys:
         - name
         - sources
         - is_missing
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                p.name,
                p.sources,
                ps.is_missing
            FROM
                packages AS p
                LEFT JOIN package_stats AS ps
                    ON p.name = ps.package
            WHERE
                p.last_seen < CURRENT_TIMESTAMP - INTERVAL '2 hours' AND
                ps.removed != TRUE
        """)

        return cursor.fetchall()


def by_name(name):
    """
    Fetches a package

    :param name:
        The name of the package

    :return:
        A dict with the package info
    """

    with connection() as cursor:
        cursor.execute("""
            SELECT
                p.*,
                ps.is_missing,
                ps.missing_error,
                ps.removed,
                ps.trending_rank,
                ps.installs_rank,
                ps.first_seen,
                ps.z_value,
                r.rendered_html AS readme_html
            FROM
                packages AS p LEFT JOIN
                package_stats AS ps ON p.name = ps.package LEFT JOIN
                readmes AS r ON p.name = r.package
            WHERE
                p.name = %s
        """, [name])
        result = cursor.fetchone()

        if not result:
            raise NotFoundError("Unable to find the package “%s”" % name)

        # Here we just grab the highest version since right now the package
        # detail page only shows the highest version number
        cursor.execute("""
            WITH version_info AS (
                SELECT
                    version,
                    -- Normalize what ST versions each version is for
                    CASE
                        WHEN sublime_text @> ARRAY['<3000', '>=3000']::varchar[]
                        THEN ARRAY[2, 3]
                        WHEN sublime_text = ARRAY['<3000']::varchar[]
                        THEN ARRAY[2]
                        WHEN sublime_text = ARRAY['>=3000']::varchar[]
                        THEN ARRAY[3]
                        ELSE ARRAY[2, 3]
                    END AS st_versions,
                    platforms,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            string_to_array(semver_without_suffix, '.')::int[] DESC,
                            semver_suffix_type DESC,
                            normalized_version DESC
                    ) AS num,
                    -- Rank each version based on semantic version
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            sublime_text,
                            platforms
                        ORDER BY
                            string_to_array(semver_without_suffix, '.')::int[] DESC,
                            semver_suffix_type DESC,
                            normalized_version DESC
                    ) AS qual_num,
                    -- Rank each version based on semantic version grouped by prerelease/stable
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            sublime_text,
                            platforms,
                            prerelease
                        ORDER BY
                            string_to_array(semver_without_suffix, '.')::int[] DESC,
                            semver_suffix_type DESC,
                            normalized_version DESC
                    ) AS type_num,
                    prerelease
                FROM
                    (
                        SELECT
                            version,
                            -- Perform the version munging that PC does for date-based versions
                            CASE
                                WHEN version ~ E'^\\\\d{4}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}\\\\.\\\\d{2}$'
                                    THEN '0.' || version
                                ELSE version
                            END AS normalized_version,
                            -- The semver without a suffix
                            REGEXP_REPLACE(version, E'^(\\\\d+\\\\.\\\\d+\\\\.\\\\d+)[^\\\\d].*$', E'\\\\1') AS semver_without_suffix,
                            -- If the version is a build, bare or prerelease
                            CASE
                                WHEN version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+-'
                                    THEN -1
                                WHEN version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\+'
                                    THEN 1
                                ELSE 0
                            END AS semver_suffix_type,
                            -- If the release is a pre-release
                            CASE
                                WHEN version ~ E'^\\\\d+\\\\.\\\\d+\\\\.\\\\d+-'
                                    THEN 1
                                ELSE 0
                            END AS prerelease,
                            -- Since you can't just join two arrays via aggregate function,
                            -- we use this construct to accomplish that
                            STRING_TO_ARRAY(STRING_AGG(DISTINCT ARRAY_TO_STRING(platforms, ','), ','), ',') platforms,
                            ARRAY_AGG(DISTINCT sublime_text) sublime_text
                        FROM
                            releases
                        WHERE
                            package = %s
                        GROUP BY
                            version
                    ) sq
                ORDER BY
                    num ASC
            )

            SELECT
                CASE
                    WHEN vi1.prerelease = 0
                    THEN vi1.version
                    ELSE null
                END AS version,
                CASE
                    WHEN vi1.prerelease = 1
                    THEN vi1.version
                    ELSE vi2.version
                END AS prerelease_version,
                vi1.platforms,
                vi1.st_versions
            FROM
                version_info AS vi1
                -- Join from the stable version to a prerelease version only if the
                -- prerelease version is higher than the stable version
                LEFT JOIN version_info AS vi2
                    ON (
                        vi1.prerelease = 0
                        AND vi2.prerelease = 1
                        AND vi2.num = 1
                        AND vi1.platforms = vi2.platforms
                        AND vi1.st_versions = vi2.st_versions
                    ) OR (
                        vi1.prerelease = 1
                        AND vi2.prerelease = 0
                        AND vi1.platforms = vi2.platforms
                        AND vi1.st_versions = vi2.st_versions
                    )
            WHERE
                -- Grab the first stable/prerelease release
                vi1.type_num = 1
                AND (
                    vi2.prerelease IS NULL
                    OR (
                        vi1.prerelease = 0
                        AND vi2.prerelease = 1
                    )
                )
            ORDER BY
                vi1.num ASC
        """, [name])

        result['versions'] = cursor.fetchall()

        result['platforms_display'] = []
        if 'windows' in result['platforms']:
            result['platforms_display'].append('Windows')
        if 'osx' in result['platforms']:
            result['platforms_display'].append('OS X')
        if 'linux' in result['platforms']:
            result['platforms_display'].append('Linux')

        result['installs'] = {
            'total': 0,
            'windows': 0,
            'osx': 0,
            'linux': 0,
            'daily': {
                'dates': [],
                'data': [
                    {
                        "platform": "Windows",
                        "totals": []
                    },
                    {
                        "platform": "OS X",
                        "totals": []
                    },
                    {
                        "platform": "Linux",
                        "totals": []
                    }
                ]
            }
        }

        today = datetime.utcnow().date()
        last_month = today - timedelta(days=45)
        iter_date = today
        row_date = last_month

        cursor.execute("""
            SELECT
                *
            FROM
                install_counts
            WHERE
                package = %s
        """, [name])
        row = cursor.fetchone()
        if row:
            result['installs']['total'] = row['unique_installs']
            result['installs']['windows'] = row['windows_unique_installs']
            result['installs']['osx'] = row['osx_unique_installs']
            result['installs']['linux'] = row['linux_unique_installs']

        cursor.execute("""
            SELECT
                *
            FROM
                daily_install_counts
            WHERE
                package = %s AND
                date BETWEEN %s AND %s
            ORDER BY
                date DESC
        """, [name, last_month, today])

        def fill_dates():
            nonlocal iter_date, row_date, result
            while iter_date > row_date:
                result['installs']['daily']['dates'].append(iter_date.strftime('%Y-%m-%d'))
                result['installs']['daily']['data'][0]['totals'].append(0)
                result['installs']['daily']['data'][1]['totals'].append(0)
                result['installs']['daily']['data'][2]['totals'].append(0)
                iter_date -= timedelta(days=1)

        for row in cursor.fetchall():
            row_date = row['date']

            fill_dates()

            result['installs']['daily']['dates'].append(row['date'].strftime('%Y-%m-%d'))
            result['installs']['daily']['data'][0]['totals'].append(row['windows_installs'])
            result['installs']['daily']['data'][1]['totals'].append(row['osx_installs'])
            result['installs']['daily']['data'][2]['totals'].append(row['linux_installs'])

            iter_date -= timedelta(days=1)
        row_date = last_month
        fill_dates()

    return result


@cache.region.cache_on_arguments()
def new(details=False, page=1, limit=10):
    """
    Fetches the most recently created packages

    :param details:
        If the description and authors should be included

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    return _common_sql(details, "", "ps.first_seen DESC", page, limit)


@cache.region.cache_on_arguments()
def updated(details=False, page=1, limit=10):
    """
    Fetches the most recently modified packages

    :param details:
        If the description and authors should be included

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    return _common_sql(details, "", "p.last_modified DESC", page, limit)


@cache.region.cache_on_arguments()
def search(terms, page=1, limit=50):
    """
    Finds all packages that match the entered search terms.

    Packages are matched against the name, author name and description, in
    that order of importance. PostgreSQL's full text search functionality is
    used when possible, falling back to simple regex matching.

    :param terms:
        A string containing words to search for

    :return:
        An array of dicts including the package name, description and
        search results rank
    """

    if terms == None or terms == '':
        return {'total': 0, 'packages': []}

    # Allow filtering packages by version compatibility and platform
    where_conditions = []
    if terms.find(':st2') != -1:
        terms = terms.replace(':st2', '')
        where_conditions.append(" AND st_versions @> ARRAY[2]")

    if terms.find(':st3') != -1:
        terms = terms.replace(':st3', '')
        where_conditions.append(" AND st_versions @> ARRAY[3]")

    if terms.find(':win') != -1:
        terms = terms.replace(':win', '')
        where_conditions.append(" AND platforms @> ARRAY['windows']::varchar[]")

    if terms.find(':osx') != -1:
        terms = terms.replace(':osx', '')
        where_conditions.append(" AND platforms @> ARRAY['osx']::varchar[]")

    if terms.find(':linux') != -1:
        terms = terms.replace(':linux', '')
        where_conditions.append(" AND platforms @> ARRAY['linux']::varchar[]")

    where_frag = ''.join(where_conditions)

    # Clean up the search terms
    terms = re.sub('\s{2,}', ' ', terms).strip()

    lower_terms = terms.lower()

    with connection() as cursor:
        cursor.execute("""
            SELECT plainto_tsquery('english', split_package_name(%s)) AS query
        """, [terms])
        query = cursor.fetchone()['query']

        # Break apart the basic parsing that PostgreSQL did
        # and add prefix and synonym support. We don't use
        # the native synonym support since it requires writing
        # a text file into a shared PostgreSQL folder and
        # that the data be re-indexed.
        parts = query.split(' & ')
        groups = []
        for part in parts:
            part = part.strip("'")
            if len(part) == 0:
                continue
            if part in synonyms:
                group = "('%s':* | '%s':*)" % (part, synonyms[part])
            else:
                group = "'%s':*" % part
            groups.append(group)
        prefix_query = ' & '.join(groups)

        if page < 1:
            page = 1
        offset = (page - 1) * limit

        output = {'packages': [], 'total': 0}

        if prefix_query != '':
            # When we indexed the data, we added three spaces in places where spaces originally did not exist
            # so that the indexer would index the words separately, but now that we are displaying data, we
            # need to collapse it back down again

            # Additionally, since we index both the split and non-split versions, we have to try to highlight
            # both variants of it, otherwise we may end up with a match that does not have a highlight

            # For the rank, we increase the weight of matches in the name by the inverse of the length of
            # the name, meaning shorter names are better matches

            # We use \002 and \003 for highlighting separators since the data transport is JSON and it doesn't
            # make sense to send HTML <b> tags since the client may not display HTML
            cursor.execute("""
                SELECT
                    p.name,
                    CASE
                        WHEN position('\002' in highlight_result(pse.split_name, query, FALSE)) <> 0
                        THEN highlight_result(pse.split_name, query, TRUE)
                        ELSE highlight_result(pse.name, query, TRUE)
                    END AS highlighted_name,
                    CASE
                        WHEN position('\002' in highlight_result(pse.split_description, query, FALSE)) <> 0
                        THEN highlight_result(pse.split_description, query, TRUE)
                        ELSE highlight_result(pse.description, query, TRUE)
                    END AS highlighted_description,
                    highlight_result_array(pse.authors, query, TRUE) AS highlighted_authors,
                    p.authors,
                    p.labels,
                    p.platforms,
                    p.st_versions,
                    p.last_modified,
                    ps.first_seen,
                    ps.is_missing,
                    ps.missing_error,
                    ps.trending_rank,
                    ps.installs_rank,
                    coalesce(ic.unique_installs, 0) unique_installs,
                    (
                        ts_rank(
                            ARRAY[0.0, 0.0, 0.0, 1.0],
                            search_vector,
                            query
                        )
                        * (20.0 / length(p.name))
                    )
                    + ts_rank(
                        ARRAY[0.05, 0.1, 0.01, 0.0],
                        search_vector,
                        query
                    )
                    + CASE
                        WHEN lower(p.name) = %s THEN 10.0
                        ELSE 0.0
                    END AS rank
                FROM
                    packages AS p LEFT JOIN
                    package_stats AS ps ON p.name = ps.package LEFT JOIN
                    install_counts AS ic ON p.name = ic.package INNER JOIN
                    package_search_entries AS pse ON pse.package = p.name,
                    to_tsquery(%s) AS query
                WHERE
                    (
                        query @@ search_vector
                        or lower(p.name) = %s
                    )
                    """ + where_frag + """
                    AND ps.removed != TRUE
                ORDER BY
                    rank DESC
                LIMIT %s
                OFFSET %s
            """, [lower_terms, prefix_query, lower_terms, limit, offset])
            output['packages'] = [row for row in cursor.fetchall()]

            cursor.execute("""
                SELECT
                    count(*) AS total
                FROM
                    packages AS p LEFT JOIN
                    package_stats AS ps ON p.name = ps.package LEFT JOIN
                    package_search_entries AS pse ON pse.package = p.name,
                    to_tsquery(%s) AS query
                WHERE
                    query @@ search_vector
                    """ + where_frag + """
                    AND ps.removed != TRUE
            """, [prefix_query])
            output['total'] = cursor.fetchone()['total']

        # With vowels and stop words, the full text search will not parse a word
        # to search for from the terms, so we use regex instead, but only on
        # the name of the package
        if prefix_query == '':
            escaped_terms = ''
            for char in terms:
                num = ord(char)
                if num > 127:
                    escaped_terms += '\\u%0.4X' % num
                else:
                    escaped_terms += re.escape(char)
            regex = "\m(%s)" % escaped_terms
            match_regex = "\m(%s[^ \n\t]*)\M" % escaped_terms

            # When we indexed the data, we added three spaces in places where spaces originally did not exist
            # so that the indexer would index the words separately, but now that we are displaying data, we
            # need to collapse it back down again
            cursor.execute("""
                SELECT
                    p.name,
                    replace(regexp_replace(pse.name, %s, E'\002\\\\1\003', 'gi'), '   ', '') AS highlighted_name,
                    p.description AS highlighted_description,
                    p.authors AS highlighted_authors,
                    p.authors,
                    p.labels,
                    p.platforms,
                    p.st_versions,
                    p.last_modified,
                    ps.first_seen,
                    ps.is_missing,
                    ps.missing_error,
                    ps.trending_rank,
                    ps.installs_rank,
                    coalesce(ic.unique_installs, 0) unique_installs,
                    (
                        CASE
                            WHEN pse.name ~* %s THEN 5.0
                            ELSE 1.0
                        END
                        * (20.0 / length(p.name)::float)
                    )
                    + CASE
                        WHEN lower(p.name) = %s THEN 10.0
                        ELSE 0.0
                    END AS rank
                FROM
                    packages AS p LEFT JOIN
                    package_stats AS ps ON p.name = ps.package LEFT JOIN
                    install_counts AS ic ON p.name = ic.package INNER JOIN
                    package_search_entries AS pse ON pse.package = p.name
                WHERE
                    (
                        regexp_replace(pse.name, ' (and|an|as) ', ' ') ~* %s
                        or lower(p.name) = %s
                    )
                    """ + where_frag + """
                    AND ps.removed != TRUE
                ORDER BY
                    rank DESC
                LIMIT %s
                OFFSET %s
            """, [match_regex, regex, lower_terms, regex, lower_terms, limit, offset])
            output['packages'] = [row for row in cursor.fetchall()]

            cursor.execute("""
                SELECT
                    count(*) AS total
                FROM
                    packages AS p LEFT JOIN
                    package_stats AS ps ON p.name = ps.package INNER JOIN
                    package_search_entries AS pse ON pse.package = p.name
                WHERE
                    regexp_replace(pse.name, ' (and|an|as|a) ', ' ') ~* %s
                    """ + where_frag + """
                    AND ps.removed != TRUE
            """, [regex])
            output['total'] = cursor.fetchone()['total']

    return output


@cache.region.cache_on_arguments()
def top(details=False, page=1, limit=10):
    """
    Fetches the most downloaded packages

    :param details:
        If the description and authors should be included

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    return _common_sql(details, "AND ic.unique_installs IS NOT NULL AND ic.unique_installs > 0", "ic.unique_installs DESC", page, limit)


def top_100_random(details=False, page=1, limit=10):
    """
    Fetches the most downloaded packages

    :param details:
        If the description and authors should be included

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    return _common_sql(details, "AND ps.installs_rank <= 100", "random() ASC", page, limit)


@cache.region.cache_on_arguments()
def trending(details=False, page=1, limit=10):
    """
    Fetches the most downloaded packages

    :param details:
        If the description and authors should be included

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    return _common_sql(details, "AND ps.z_value IS NOT NULL", "ps.trending_rank ASC", page, limit)


def _common_sql(details, where, order_by, page, limit):
    """
    Fetches a standard set of info about packages for the purposes of
    allowing users to browse around the site

    :param details:
        If the description and authors should be included along with a total
        number of packages without a limit

    :param where:
        A SQL fragment of WHERE conditions, must start with "AND"

    :param order_by:
        A SQL fragment of the ORDER BY clause to use

    :param page:
        Which page (int) of the packages to return

    :param limit:
        The (int) maximum number of packages to list

    :return:
        An array of dict object, each representing the info for a package
    """

    if page < 1:
        page = 1
    offset = (page - 1) * limit

    with connection() as cursor:

        # Standard columns
        columns = [
            'p.name',
            'p.platforms',
            'p.st_versions',
            'ps.trending_rank',
            'ps.installs_rank',
            'coalesce(ic.unique_installs, 0) unique_installs'
        ]
        # "Details" columns
        if details:
            columns.extend([
                'p.authors',
                'p.description',
                'p.last_modified',
                'ps.first_seen',
                'ps.is_missing',
                'ps.missing_error'
            ])

        columns_frag = ", ".join(columns)

        cursor.execute("""
            SELECT
                """ + columns_frag + """
            FROM
                packages AS p LEFT JOIN
                package_stats AS ps ON p.name = ps.package LEFT JOIN
                install_counts AS ic ON p.name = ic.package
            WHERE
                ps.is_missing != TRUE AND
                ps.removed != TRUE
                """ + where + """
            ORDER BY
                """ + order_by + """
            LIMIT %s
            OFFSET %s
        """, [limit, offset])

        output = cursor.fetchall()

        if details:
            cursor.execute("""
                SELECT
                    count(*) AS total
                FROM
                    packages AS p LEFT JOIN
                    package_stats AS ps ON p.name = ps.package LEFT JOIN
                    install_counts AS ic ON p.name = ic.package
                WHERE
                    ps.is_missing != TRUE AND
                    ps.removed != TRUE
                    """ + where)
            output = {
                'packages': output,
                'total': cursor.fetchone()['total']
            }

        return output
