import json
import psycopg2
import psycopg2.extras
from datetime import date, time, datetime, timedelta
from cryptopan import CryptoPan

anonymizer = CryptoPan('dskalsd903jklas2ksifnamcjkld903j')

connection_params = {
	'database': 'package_control',
	'user': 'postgres',
	'host': '127.0.0.1',
	'connection_factory': psycopg2.extras.RealDictConnection
}
con = psycopg2.connect(**connection_params)
cur = con.cursor()

midnight = time(0, 0, 0)
eleven_59 = time(23, 59, 59)

today = date.today()
offset = 0

output = []
while offset < 30:
	offset += 1
	day = today - timedelta(days=offset)

	start = datetime.combine(day, midnight)
	end = datetime.combine(day, eleven_59)
	cur.execute("""
		SELECT *
		FROM usage
		WHERE date_time BETWEEN %s AND %s
		ORDER BY md5(date_time::varchar) DESC
		LIMIT 500
	""", [start, end])

	for row in cur:
		del row['usage_id']
		row['ip'] = anonymizer.anonymize(row['ip'])
		output.append(row)

class DateTimeEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime('%Y-%m-%d %H:%M:%S')

		return json.JSONEncoder.default(self, obj)

with gzip.open('../cleaned_data.json.gz', 'wb') as f:
	f.write(json.dumps(output, indent=2, cls=DateTimeEncoder).encode('utf-8'))