from http.client import HTTPResponse, IncompleteRead

from ..console_write import console_write


class DebuggableHTTPResponse(HTTPResponse):

    """
    A custom HTTPResponse that formats debugging info for Sublime Text
    """

    _debug_protocol = 'HTTP'

    def __init__(self, sock, debuglevel=0, method=None, **kwargs):
        # We have to use a positive debuglevel to get it passed to here,
        # however we don't want to use it because by default debugging prints
        # to the stdout and we can't capture it, so we use a special -1 value
        if debuglevel == 5:
            debuglevel = -1
        HTTPResponse.__init__(self, sock, debuglevel=debuglevel, method=method)

    def begin(self):
        return_value = HTTPResponse.begin(self)
        if self.debuglevel == -1:
            # Python 2
            if hasattr(self.msg, 'headers'):
                headers = [line.rstrip() for line in self.msg.headers]
            # Python 3
            else:
                headers = []
                for header in self.msg:
                    headers.append("%s: %s" % (header, self.msg[header]))

            versions = {
                9: 'HTTP/0.9',
                10: 'HTTP/1.0',
                11: 'HTTP/1.1'
            }
            status_line = '%s %s %s' % (versions[self.version], str(self.status), self.reason)
            headers.insert(0, status_line)

            indented_headers = '\n  '.join(headers)
            console_write(
                '''
                Urllib %s Debug Read
                  %s
                ''',
                (self._debug_protocol, indented_headers)
            )

        return return_value

    def is_keep_alive(self):
        # Python 2
        if hasattr(self.msg, 'headers'):
            connection = self.msg.getheader('connection')
        # Python 3
        else:
            connection = self.msg['connection']
        if connection and connection.lower() == 'keep-alive':
            return True
        return False

    def read(self, *args):
        try:
            return HTTPResponse.read(self, *args)
        except (IncompleteRead) as e:
            return e.partial
