import json
import gzip
import psycopg2
import psycopg2.extras
from datetime import date, time, datetime, timedelta
from dateutil import parser

connection_params = {
    'database': 'package_control',
    'user': 'sublime',
    'password': 's9esWe9a4ubrAs8a',
    'host': '127.0.0.1',
    'connection_factory': psycopg2.extras.RealDictConnection
}
con = psycopg2.connect(**connection_params)
cur = con.cursor()

cur.execute("TRUNCATE usage")

with gzip.open('../cleaned_data.json.gz', 'rb') as f:
    rows = json.loads(str(f.read(), encoding='utf-8'))
    cur.executemany("""
        INSERT INTO usage (
            ip,
            date_time,
            operation,
            package,
            version,
            old_version,
            package_control_version,
            user_agent,
            sublime_version,
            sublime_platform
        ) VALUES (
            %(ip)s,
            %(date_time)s,
            %(operation)s,
            %(package)s,
            %(version)s,
            %(old_version)s,
            %(package_control_version)s,
            %(user_agent)s,
            %(sublime_version)s,
            %(sublime_platform)s
        )
    """, rows)

# Calculate all of the other statistics and info from the usage table.
# We maintain these tables as usage data is recorded when running in
# production since the production DB has tens of millions of rows.
cur.execute("""
    INSERT INTO unique_package_installs
    SELECT DISTINCT ip, package, sublime_platform
    FROM usage
    WHERE operation = 'install'
""")

cur.execute("""
    INSERT INTO ips
    SELECT DISTINCT ip, sublime_platform
    FROM usage
""")

cur.execute("""
    INSERT INTO install_counts (package, unique_installs)
    SELECT package, count(ip)
    FROM unique_package_installs
    GROUP BY package
""")

cur.execute("""
    UPDATE install_counts
    SET installs = u.installs
    FROM (SELECT package, count(*) AS installs
          FROM usage
          WHERE operation = 'install'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET osx_installs = u.installs
    FROM (SELECT package, count(*) AS installs
          FROM usage
          WHERE operation = 'install' and
                sublime_platform = 'osx'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET osx_unique_installs = u.installs
    FROM (SELECT package, count(ip) AS installs
          FROM unique_package_installs
          WHERE sublime_platform = 'osx'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET windows_installs = u.installs
    FROM (SELECT package, count(*) AS installs
          FROM usage
          WHERE operation = 'install' and
                sublime_platform = 'windows'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET windows_unique_installs = u.installs
    FROM (SELECT package, count(ip) AS installs
          FROM unique_package_installs
          WHERE sublime_platform = 'windows'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET linux_installs = u.installs
    FROM (SELECT package, count(*) AS installs
          FROM usage
          WHERE operation = 'install' and
                sublime_platform = 'linux'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    UPDATE install_counts
    SET linux_unique_installs = u.installs
    FROM (SELECT package, count(ip) AS installs
          FROM unique_package_installs
          WHERE sublime_platform = 'linux'
          GROUP BY package) AS u
    WHERE u.package = install_counts.package
""")

cur.execute("""
    INSERT INTO first_installs
    SELECT package, min(date_time)
    FROM usage
    WHERE operation = 'install'
    GROUP BY package
""")

con.commit()

cur.execute("SELECT min(date_time) AS date_time FROM usage")
first_date_time = cur.fetchone()['date_time']

first_date = first_date_time.date()
today = date.today() - timedelta(days=1)

begin = time(0, 0, 0)
end = time(23, 23, 59)

cur.execute("SELECT name FROM packages")
valid_packages = [row['name'] for row in cur]

loop_date = first_date
while loop_date < today:
    cur.execute("""
        SELECT
            package,
            sublime_platform,
            count(usage_id) AS installs
        FROM
            usage
        WHERE
            date_time BETWEEN %s and %s
        GROUP BY
            package,
            sublime_platform
    """, [datetime.combine(loop_date, begin), datetime.combine(loop_date, end)])

    package_info = {}
    for row in cur:
        package = row['package']
        if package not in valid_packages:
            continue
        if package not in package_info:
            package_info[package] = {
                'osx': 0,
                'windows': 0,
                'linux': 0
            }
        package_info[package][row['sublime_platform']] = row['installs']

    for package in package_info:
        info = package_info[package]

        cur.execute("""
            INSERT INTO daily_install_counts (
                    date,
                    package,
                    installs,
                    osx_installs,
                    windows_installs,
                    linux_installs
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
        """, [
            loop_date,
            package,
            info['osx'] + info['windows'] + info['linux'],
            info['osx'],
            info['windows'],
            info['linux']
        ])
        print("%s - %s" % (loop_date, package))

    con.commit()

    loop_date = loop_date + timedelta(days=1)

