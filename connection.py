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

import time
import http.client
import re
import socket
import urllib.parse
from urllib.parse import urlparse, urlunparse
import copy

import chardet
from dbmsmoles import DbmsMole
from exceptions import *

class HttpRequester:
    headers =  {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

    accepted_methods = ['GET', 'POST']

    def __init__(self, url = None, vulnerable_param = None, delay = 0, method = 'GET', cookie = None, max_retries=3):
        self.encoding = None
        self.delay = delay
        self.method = None
        self.max_retries = max_retries
        self.headers = HttpRequester.headers.copy()
        self.proto = None
        self.host = None
        self.path = None
        self.get_parameters = []
        self.post_parameters = []
        self.vulnerable_param = None
        self.vulnerable_param_group = None
        self.set_method(method)
        if url is not None:
            self.set_url(url)
        if vulnerable_param is not None:
            self.set_vulnerable_param(method, vulnerable_param)
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
        return DbmsMole.remove_errors(to_ret)

    # Tries to remove the query from the result html.
    def filter(self, data, params):
        try:
            for i in params:
                if i[0] == self.vulnerable_param:
                    return self.ireplace(i[1], '', data) if 'and' in i[1].lower() or 'order by' in i[1].lower() else data
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

    def _normalize_params(self, params):
        params = list(filter(lambda x: len(x[0]) > 0, params))
        for i in params:
            if len(i) == 1:
                i.append('')
        return params

    def do_request(self, query):
        get_params = copy.deepcopy(self.get_parameters)
        post_params = copy.deepcopy(self.post_parameters)
        if self.vulnerable_param_group == 'GET':
            get_params = self._add_query_to_param(get_params, query)
            filter_params = get_params
        else:
            post_params = self._add_query_to_param(post_params, query)
            filter_params = post_params
        get_params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in get_params)
        post_params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in post_params)

        try:
            if self.proto == 'https':
                connection = http.client.HTTPSConnection(self.host)
            else:
                connection = http.client.HTTPConnection(self.host)
        except (http.client.NotConnected,
                http.client.InvalidURL,
                http.client.UnknownProtocol,
                http.client.BadStatusLine) as e:
            raise ConnectionException(str(e))

        for i in range(self.max_retries):
            try:
                connection.request(self.method, self.path + '?' + get_params, post_params, self.headers)
                resp = connection.getresponse()
                data = self.decode(resp.read())
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

        return self.filter(data, filter_params)

    def request(self, query):
        time.sleep(self.delay)
        data = self.do_request(query)
        return data

    def is_initialized(self):
        return self.host is not None and self.vulnerable_param is not None

    def set_url(self, url):
        parsed = urlparse(url)
        self.proto = parsed.scheme
        self.host = parsed.netloc
        self.path = parsed.path
        if parsed.query:
            self.get_parameters = self._normalize_params(list(t.split('=', 1) for t in parsed.query.split('&')))
        else:
            self.get_parameters = []
        self.post_parameters = []
        self.headers['Host'] = parsed.netloc

    def get_url(self):
        get_params = '&'.join(x[0] + '=' + x[1] for x in self.get_parameters)
        return urlunparse((self.proto, self.host, self.path, '', get_params, ''))

    def set_method(self, method):
        if method not in self.accepted_methods:
            raise InvalidMethodException('[-] Error: ' + method + ' is invalid! Only GET supported.')
        self.method = method
        if method == 'POST':
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            if 'Content-Type' in self.headers:
                del self.headers['Content-Type']
        self.vulnerable_param = None
        self.vulnerable_param_group = None

    def set_post_params(self, param_string):
        if '=' not in param_string:
            param_string_lst = []
        else:
            param_string_lst = list(t.split('=', 1) for t in param_string.split('&'))
        param_string_lst = self._normalize_params(param_string_lst)
        self.post_parameters = param_string_lst

    def get_post_params(self):
        return '&'.join(a + '=' + b for a,b in self.post_parameters)

    def set_vulnerable_param(self, method, vulnerable_param):
        if vulnerable_param is not None:
            if method == 'GET' and vulnerable_param not in (x[0] for x in self.get_parameters):
                raise InvalidParamException(vulnerable_param + ' is not present in the given URL.')
            if method == 'POST' and vulnerable_param not in (x[0] for x in self.post_parameters):
                raise InvalidParamException(vulnerable_param + ' is not in the POST parameters.')
            self.vulnerable_param = vulnerable_param
        self.vulnerable_param_group = method

    def get_vulnerable_param(self):
        return (self.vulnerable_param_group, self.vulnerable_param)
