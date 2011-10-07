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

class HttpRequester:
    headers =  {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'text/html;q=0.9',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    def __init__(self, url, proxy = '', timeout = 0, method = 'GET', cookie = None):
        self.url = url
        self.timeout = timeout
        if method not in ['GET',  'POST']:
            raise Exception('[-] Error: ' + method + ' is invalid! Only GET and POST supported')
        self.method = method
        if len(proxy) > 0:
            ip = self.get_ip()
            proxy_support = urllib.request.ProxyHandler({'http': proxy})
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)
            if not self.is_anonymous(ip):
                raise Exception('[-] Error: Proxy is not anonymous!')
        self.checked_diff = False
        self.headers = HttpRequester.headers
        if cookie:
            self.headers['Cookie'] = cookie

    def get_ip(self):
        input = urllib.request.urlopen('http://checker.samair.ru/').read()
        return input.split('<b>IP detected: ')[1].replace('<font color="#008000">', '').split('</font>')[0].strip()

    def is_anonymous(self, ip):
        input = urllib.request.urlopen('http://checker.samair.ru/').read()
        return not ip in input and 'high-anonymous (elite) proxy' in input

    def do_request(self, params):
        params = (t.split('=', 1) for t in params.split('&'))
        params = '&'.join(a + '=' + urllib.parse.quote(b) for a, b in params)
        if self.method == 'GET':
            request = urllib.request.Request(self.url + '?' + params, None, self.headers)
        else:
            request = urllib.Request(self.url, params, self.headers)
        return urllib.request.urlopen(request).read()

    def request(self, params):
        time.sleep(self.timeout)	
        data = self.do_request(params)
        return data
