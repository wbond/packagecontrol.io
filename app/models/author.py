from ..lib.connection import connection
from .. import cache


@cache.region.cache_on_arguments()
def list(details=False, page=1, limit=10):
    """
    Fetches the most prolific authors

    :param details:
        If the result should be a dict with `authors` and `total` keys
        instead of just a list of author dict objects

    :param page:
        The (int) page of authors to list

    :param limit:
        The (int) maximum number of authors to list

    :return:
        A list of dicts, with the keys:
          `name`
          `packages`
    """

    if page < 1:
        page = 1
    offset = (page - 1) * limit

    with connection() as cursor:
        cursor.execute("""
            SELECT
                author AS name,
                COUNT(name) AS packages
            FROM
                (
                    SELECT
                        *,
                        unnest(authors) AS author
                    FROM
                        packages
                ) AS sq
            GROUP BY
                author
            ORDER BY
                COUNT(name) DESC,
                LOWER(author) ASC
            LIMIT %s
            OFFSET %s
        """, [limit, offset])
        output = cursor.fetchall()

        if details:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total
                FROM
                    (
                        SELECT
                            DISTINCT unnest(authors)
                        FROM
                            packages
                    ) AS sq
                """)
            output = {
                'authors': output,
                'total': cursor.fetchone()['total']
            }

    return output


def load(author):
    """
    Fetches an author

    :param author:
        The name of the author

    :return:
        An dict with the author info
    """

    with connection() as cursor:
        result = {'name': author}

        cursor.execute("""
            SELECT
                p.name,
                p.description,
                p.authors,
                p.labels,
                p.platforms,
                p.st_versions,
                p.last_modified,
                p.last_seen,
                ps.is_missing,
                ps.needs_review,
                ps.trending_rank,
                ps.installs_rank,
                ps.first_seen,
                ps.z_value,
                ic.unique_installs
            FROM
                packages AS p LEFT JOIN
                package_stats AS ps ON ps.package = p.name LEFT JOIN
                install_counts AS ic ON p.name = ic.package
            WHERE
                p.authors @> ARRAY[%s]::varchar[]
            ORDER BY
                p.name ASC
        """, [author])
        result['packages'] = [row for row in cursor.fetchall()]

    return result

