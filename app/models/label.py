from ..lib.connection import connection
from .. import cache


@cache.region.cache_on_arguments()
def list(details=False, page=1, limit=10):
    """
    Fetches the most used labels

    :param details:
        If the result should be a dict with `authors` and `total` keys
        instead of just a list of author dict objects

    :param page:
        The (int) page of labels to list

    :param limit:
        The (int) maximum number of labels to list

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
                l.label AS name,
                COUNT(p.name) AS packages
            FROM
                packages AS p INNER JOIN
                (
                    SELECT
                        DISTINCT unnest(labels) AS label
                    FROM
                        packages
                ) AS l ON p.labels @> ARRAY[l.label]::varchar[]
            GROUP BY
                l.label
            ORDER BY
                COUNT(p.name) DESC
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
                            DISTINCT unnest(labels) AS label
                        FROM
                            packages
                    ) AS sq
                """)
            output = {
                'labels': output,
                'total': cursor.fetchone()['total']
            }

    return output


def load(name):
    """
    Fetches a label

    :param name:
        The name of the label

    :return:
        An dict with the label info
    """

    with connection() as cursor:
        result = {'name': name}

        cursor.execute("""
            SELECT
                p.name,
                p.description,
                p.author,
                p.labels,
                p.platforms,
                p.st_versions,
                p.last_modified,
                p.last_seen,
                ps.is_missing,
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
                p.labels @> ARRAY[%s]::varchar[]
            ORDER BY
                p.name ASC
        """, [name])
        result['packages'] = [row for row in cursor.fetchall()]

    return result

