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

from urllib.parse import urlparse, urlencode

class Request():
    def __init__(self, method, url, get_parameters={}, post_parameters={}, cookie={}, headers={}):
        self.method = method
        parsed_url = urlparse(url)
        self.proto = parsed_url.scheme
        self.host = parsed_url.netloc
        self.path = parsed_url.path
        self.get_parameters = get_parameters
        self.post_parameters = post_parameters
        self.cookie = cookie
        self.headers = headers
        self.headers["Cookie"] = urlencode(cookie)

    def str_url(self):
        return self.proto + self.host + self.path + '?' + urlencode(self.get_parameters)

    def str_uri(self):
        return self.path + '?' + urlencode(self.get_parameters)
