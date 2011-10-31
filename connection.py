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
import copy

class HttpRequester:
    headers =  {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    def __init__(self, url, vulnerable_param, timeout = 0, method = 'GET', cookie = None, max_retries=3):
        self.encoding = None
        self.timeout = timeout
        if method not in ['GET']:
            raise Exception('[-] Error: ' + method + ' is invalid! Only GET supported.')
        self.method = method
        self.max_retries = max_retries
        self.headers = HttpRequester.headers
        parsed = urlparse(url)
        self.host = parsed.netloc
        self.path = parsed.path
        self.get_parameters = list(t.split('=', 1) for t in parsed.query.split('&'))
        self.post_parameters = []
        self.headers['Host'] = parsed.netloc
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

    def _add_query_to_param(self, parameters, query):
        for i in range(len(parameters)):
            if parameters[i][0] == self.vulnerable_param:
                parameters[i][1] = parameters[i][1] + query
                return parameters
        return None

    def do_request(self, query):
        #params = list(t.split('=', 1) for t in params.split('&'))
        get_params = copy.deepcopy(self.get_parameters)
        post_params = copy.deepcopy(self.post_parameters)
        if self.method == 'GET':
            get_params = self._add_query_to_param(get_params, query)
            params = get_params
        else:
            post_params = self._add_query_to_param(post_params, query)
            params = post_params
        get_params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in get_params)
        post_params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in post_params)
        
        exception = Exception()
        connection = http.client.HTTPConnection(self.host)
        for i in range(self.max_retries):
            try:
                connection.request('GET', self.path + '?' + get_params, post_params, self.headers)
                resp = connection.getresponse()
                data = self.decode(resp.read())
                return self.filter(data, params)
            except Exception as ex:
                exception = ex
        raise exception

    def request(self, query):
        time.sleep(self.timeout)	
        data = self.do_request(query)
        return data
