# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
# Developed by: Nasel(http://www.nasel.com.ar)
#
# Authors:
# Matías Fontanini
# Santiago Alessandri
# Gastón Traberg

import http.client
import socket
from urllib.parse import urlencode, urlparse

from moleexceptions import ConnectionException
from connection.response import Response

class BaseRequestSender():

    def __init__(self):
        self.follow_redirects = False
        self.max_retries = 3

    def __str__(self):
        pass

    def fetch_data(self, request, connection):
        pass

    def send(self, request):
        try:
            if request.proto == 'https':
                connection = http.client.HTTPSConnection(request.host)
            else:
                connection = http.client.HTTPConnection(request.host)
        except (http.client.NotConnected,
                http.client.InvalidURL,
                http.client.UnknownProtocol,
                http.client.BadStatusLine) as e:
            raise ConnectionException(str(e))

        for _ in range(self.max_retries):
            try:
                data = self.fetch_data(request, connection)
                break
            except (socket.error,
                    socket.timeout,
                    http.client.IncompleteRead,
                    http.client.CannotSendRequest,
                    http.client.CannotSendHeader,
                    http.client.ResponseNotReady,
                    http.client.BadStatusLine) as ex:
                data = None
                exception = ex

        if data is None:
            raise ConnectionException(str(exception))

        return Response(data)

class HttpRequestSender(BaseRequestSender):
    
    def fetch_data(self, request, connection):
        connection.request(request.method,
                           request.str_uri(),
                           urlencode(request.post_parameters),
                           request.headers)
        resp = connection.getresponse()
        resp_headers = dict(resp.getheaders())
        while self.follow_redirects and resp.getcode() == 302 and 'Location' in resp_headers:
            resp.read() # Need to read whole request before sending a new one
            parsed = urlparse(resp_headers["Location"])
            request.headers["Host"] = parsed.netloc
            connection.request('GET', parsed.path, None, request.headers)
            resp = connection.getresponse()
            resp_headers = dict(resp.getheaders())
        return resp.read()

    def __str__(self):
        return 'httpsender'

class HttpHeadRequestSender(BaseRequestSender):
    def fetch_data(self, request, connection):
        connection.request('HEAD',
                           request.str_uri(),
                           urlencode(request.post_parameters),
                           request.headers)
        resp = connection.getresponse()
        headers = dict(resp.getheaders())
        output = ''
        for header in headers:
            output += '<div>{0} {1}</div>\n'.format(header, headers[header])
        return '<html><body>{0}</body></html>'.format(output).encode()

    def __str__(self):
        return 'headsender'
