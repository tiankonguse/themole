#!/usr/bin/python3
# 
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

import urllib.request, urllib.error, urllib.parse, time, difflib
import http.client
from urllib.parse import urlparse

class HttpRequester:
    headers =  {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    def __init__(self, url, timeout = 0, method = 'GET', cookie = None, max_retries=3):
        self.url = url
        self.timeout = timeout
        if method not in ['GET',  'POST']:
            raise Exception('[-] Error: ' + method + ' is invalid! Only GET and POST supported.')
        self.method = method
        self.max_retries = max_retries
        self.headers = HttpRequester.headers
        self.headers['Host'] = urlparse(url).netloc
        if cookie:
            self.headers['Cookie'] = cookie

    def do_request(self, params):
        params = (t.split('=', 1) for t in params.split('&'))
        params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in params)
        params = params.replace('union', 'unIOn')
        params = params.replace('UNION', 'unIOn')
        exception = Exception()
        if self.method == 'GET':
            request = urllib.request.Request(self.url + '?' + params, None, self.headers)
        else:
            request = urllib.Request(self.url, params, self.headers)
        for i in range(self.max_retries):
            try:
                return urllib.request.urlopen(request).read()
            except urllib.error.HTTPError as ex:
                exception = ex 
                pass
            except urllib.error.URLError as ex:
                exception = ex
                pass
            except http.client.BadStatusLine:
                pass
            except http.client.IncompleteRead:
                pass
        try:
            if exception.code in [404, 500]:
                return b'<html><body></body></html>'
        except AttributeError:
            pass
        raise exception

    def request(self, params):
        time.sleep(self.timeout)	
        data = self.do_request(params)
        return data
