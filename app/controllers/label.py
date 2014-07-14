from bottle import route

from ..models import label
from ..render import render


@route('/browse/labels/<name:re:(.*)>', name='label')
def label_controller(name):
    # URLs are always latin1 because of WSGI, but browsers tend to send UTF-8
    name = bytes(name, 'latin1').decode('utf-8', errors='ignore')

    data = label.load(name)

    return render('label', data)
