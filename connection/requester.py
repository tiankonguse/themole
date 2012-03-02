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

import urllib.parse
import time
import chardet
import encodings

from moleexceptions import InvalidMethodException, InvalidParamException, EncodingNotFound
from connection.request import Request
from filters import QueryFilterManager, RequestFilterManager, ResponseFilterManager


class Requester(object):

    headers = {
        'User-Agent': 'Mozilla/The Mole (themole.nasel.com.ar)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

    accepted_methods = ['GET', 'POST', 'Cookie']

    def __init__(self, sender, url=None, vulnerable_param=None, delay=0, method='GET', cookie=''):
        self.__sender = sender
        self.__delay = delay
        self.__method = None
        self.__headers = Requester.headers.copy()
        self.__url = None
        self.__get_parameters = {}
        self.__post_parameters = {}
        self.__cookie_parameters = {}
        self.__vulnerable_param = None
        self.__vulnerable_param_group = None
        self.__query_filters = QueryFilterManager()
        self.__request_filters = RequestFilterManager()
        self.__response_filters = ResponseFilterManager()
        self.__encoding = None
        self.method = method
        if url is not None:
            self.url = url
        if vulnerable_param is not None:
            self.set_vulnerable_param(method, vulnerable_param)
        if cookie:
            self.cookie_parameters = cookie
        self.__response_filters.add_filter('script_error_filter', [])
        self.__response_filters.add_filter('html_validator', [])

    def decode(self, data):
        if self.__encoding is not None:
            try:
                to_ret = data.decode(self.__encoding)
            except (UnicodeDecodeError, TypeError):
                self.__encoding = None

        if self.__encoding is None:
            self.__encoding = chardet.detect(data)['encoding']
            try:
                to_ret = data.decode(self.__encoding)
            except (UnicodeDecodeError, TypeError):
                self.__encoding = None

        if self.__encoding is None:
            self.__encoding = self.guess_encoding(data)
            if self.__encoding:
                raise EncodingNotFound('Try using the "encoding" command.')
            try:
                to_ret = data.decode(self.__encoding)
            except (UnicodeDecodeError, TypeError):
                self.__encoding = None

        if self.__encoding is None:
            raise EncodingNotFound('Try using the "encoding" command.')

        return to_ret
        #return DbmsMole.remove_errors(to_ret)

    def request(self, query):
        """Make the request applying the filters and return the response.
        
        @param query: String containing the query to inject in the
        vulnerable param.
        @return: String containing the response in html format.
        
        """

        query = self.__query_filters.apply_filters(query)

        get_params = self.__get_parameters.copy()
        post_params = self.__post_parameters.copy()
        cookie_params = self.__cookie_parameters.copy()
        headers = self.__headers.copy()
        if self.__vulnerable_param_group == 'GET':
            get_params[self.__vulnerable_param] += query
        elif self.__vulnerable_param_group == 'POST':
            post_params[self.__vulnerable_param] += query
        else:
            cookie_params[self.__vulnerable_param] += query

        request = Request(self.__method,
                          self.__url,
                          get_params,
                          post_params,
                          cookie_params,
                          headers)

        self.__request_filters.apply_filters(request)

        time.sleep(self.__delay)

        response = self.__sender.send(request)

        response.content = self.decode(response.content)

        self.__response_filters.apply_filters(response)

        return response.content

    def is_initialized(self):
        return self.__url is not None and self.__vulnerable_param is not None

    @property
    def sender(self):
        return self.__sender

    @sender.setter
    def sender(self, sender):
        self.__sender = sender

    @property
    def delay(self):
        return self.__delay

    @delay.setter
    def delay(self, delay):
        self.__delay = delay

    @property
    def method(self):
        return self.__method

    @method.setter
    def method(self, method):
        if method not in Requester.accepted_methods:
            raise InvalidMethodException('Error: {0} is invalid!'.format(self.__method))
        self.__method = method
        if method == 'POST':
            self.__headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            if 'Content-Type' in self.__headers:
                del self.__headers['Content-Type']
        self.__vulnerable_param = None
        self.__vulnerable_param_group = None

    @property
    def url(self):
        return self.__url + '?' + urllib.parse.urlencode(self.__get_parameters, True)

    @url.setter
    def url(self, url):
        parsed = urllib.parse.urlparse(url)
        self.__url = urllib.parse.urlunsplit((parsed.scheme,
                                              parsed.netloc,
                                              parsed.path,
                                              '',
                                              ''))
        self.get_parameters = parsed.query
        self.__post_parameters = {}

    @property
    def get_parameters(self):
        return self.__get_parameters
        
    @property
    def encoding(self):
        return self.__encoding
    
    @encoding.setter
    def encoding(self, new_encoding):
        self.__encoding = new_encoding

    @get_parameters.setter
    def get_parameters(self, get_params):
        self.__get_parameters = urllib.parse.parse_qs(get_params, True)
        for param in self.__get_parameters:
            self.__get_parameters[param] = self.__get_parameters[param][-1]

    @property
    def post_parameters(self):
        return self.__post_parameters

    @post_parameters.setter
    def post_parameters(self, post_params):
        self.__post_parameters = urllib.parse.parse_qs(post_params, True)
        for param in self.__post_parameters:
            self.__post_parameters[param] = self.__post_parameters[param][-1]

    @property
    def cookie_parameters(self):
        return self.__cookie_parameters

    @cookie_parameters.setter
    def cookie_parameters(self, cookie_params):
        self.__cookie_parameters = urllib.parse.parse_qs(cookie_params, True)
        for param in self.__cookie_parameters:
            self.__cookie_parameters[param] = self.__cookie_parameters[param][-1]

    def get_vulnerable_param(self):
        return (self.__vulnerable_param_group, self.__vulnerable_param)

    def set_vulnerable_param(self, method, vulnerable_param):
        if vulnerable_param is not None:
            if method == 'GET' and vulnerable_param not in self.__get_parameters:
                raise InvalidParamException('{0} is not present in the given URL.'.format(vulnerable_param))
            if method == 'POST' and vulnerable_param not in self.__post_parameters:
                raise InvalidParamException('{0} is not in the POST parameters.'.format(vulnerable_param))
            if method == 'Cookie' and vulnerable_param not in self.__cookie_parameters:
                raise InvalidParamException('{0} is not in the Cookie parameters.'.format(vulnerable_param))
            self.__vulnerable_param = vulnerable_param
        self.__vulnerable_param_group = method

    def guess_encoding(self, data):
        for enc in set(encodings.aliases.aliases.values()):
            try:
                data.decode(enc)
                return enc
            except UnicodeDecodeError:
                pass
        return None

    @property
    def query_filters(self):
        return self.__query_filters

    @query_filters.setter
    def query_filters(self, query_filters):
        self.__query_filters = query_filters

    @property
    def request_filters(self):
        return self.__request_filters

    @request_filters.setter
    def request_filters(self, request_filters):
        self.__request_filters = request_filters

    @property
    def response_filters(self):
        return self.__response_filters

    @response_filters.setter
    def response_filters(self, response_filters):
        self.__response_filters = response_filters
