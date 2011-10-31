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
import chardet, re
from dbmsmoles import DbmsMole
from socket import error

class HttpRequester:
    headers =  {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self, url = None, vulnerable_param = None, timeout = 0, method = 'GET', cookie = None, max_retries=3):
        self.encoding = None
        self.timeout = timeout
        if method not in ['GET',  'POST']:
            raise Exception('[-] Error: ' + method + ' is invalid! Only GET and POST supported.')
        self.method = method
        self.max_retries = max_retries
        self.headers = HttpRequester.headers
        if url is not None:
            self.set_url(url)
        if vulnerable_param is not None:
            self.vulnerable_param = vulnerable_param
        if cookie:
            self.headers['Cookie'] = cookie

    def decode(self, data):
        if self.encoding is None:
            self.encoding = chardet.detect(data)['encoding']
        try:
            to_ret = data.decode(self.encoding)
        except UnicodeDecodeError:
            self.encoding = chardet.detect(data)['encoding']
            to_ret = data.decode(self.encoding)
        if not '<html' in to_ret and not '<HTML' in to_ret:
            to_ret = '<html><body></body></html>' + to_ret
        return DbmsMole.remove_errors(to_ret)

    # Tries to remove the query from the result html.
    def filter(self, data, params):
        try:
            for i in params:
                if i[0] == self.vulnerable_param:
                    return self.ireplace(i[1], '', data) if 'and' in i[1].lower() else data
        except ValueError:
            pass
        return data

    def ireplace(self, old, new, text):
        idx = 0
        while idx < len(text):
            index_l = text.lower().find(old.lower(), idx)
            if index_l == -1:
                return text
            text = text[:index_l] + new + text[index_l + len(old):]
            idx = index_l + len(old)
        return text

    def do_request(self, params):
        params = list(t.split('=', 1) for t in params.split('&'))
        params_enc = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in params)
        exception = Exception()
        if self.method == 'GET':
            request = urllib.request.Request(self.url + '?' + params_enc, None, self.headers)
        else:
            request = urllib.Request(self.url, params_enc, self.headers)
        for i in range(self.max_retries):
            try:
                data = self.decode(urllib.request.urlopen(request).read())
                return self.filter(data, params)
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
            except error:
                pass
        try:
            if exception.code in [404, 500]:
                return '<html><body></body></html>'
        except AttributeError:
            pass
        raise exception

    def request(self, params):
        time.sleep(self.timeout)
        data = self.do_request(params)
        return data

    def set_url(self, url):
        self.url = url
        self.headers['Host'] = urlparse(url).netloc
