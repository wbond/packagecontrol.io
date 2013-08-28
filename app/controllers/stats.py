from datetime import datetime, timedelta

from bottle import route

from ..models import system_stats
from ..render import render


@route('/stats', name='stats')
def stats_controller():
    data = system_stats.fetch('1 days')
    data['date'] = datetime.utcnow().replace(hour=0, minute=0, second=0) - timedelta(days=2)

    return render('stats', data)
