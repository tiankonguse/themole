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

import re, sre_constants
from exceptions import *
from htmlfilters.base import *

class BaseRegexHTMLFilter(HTMLFilter):
    def __init__(self, filter_str, replacement):
        self.replacement = replacement
        try:
            self.regex = re.compile(filter_str)
        except sre_constants.error as ex:
            raise FilterCreationError(str(ex))
    
    def filter(self, data):
        return self.regex.sub(self.replacement, data)
        
    def parse_params(self, params):
        params = ' '.join(params)
        if not params.startswith("'"):
            raise FilterCreationError('Regex must be quoted using single quotes.')
        quotes = list(re.finditer(r"(?<!\\)\'", params))
        if len(quotes) < 2:
            raise FilterCreationError('Regex must be quoted using single quotes.')
        end = quotes[1].start()
        return list(filter(lambda x: len(x) > 0, [params[1:end], params[end+2:]]))

class RemoverRegexHTMLFilter(BaseRegexHTMLFilter):
    def __init__(self, params):
        params = self.parse_params(params)
        if len(params) != 1:
            raise FilterCreationError('Expected regex as argument.')
        BaseRegexHTMLFilter.__init__(self, params[0], '')

class ReplacerRegexHTMLFilter(BaseRegexHTMLFilter):
    def __init__(self, params):
        params = self.parse_params(params)
        if len(params) != 2:
            raise FilterCreationError('Expected regex and replacement string as arguments.')
        BaseRegexHTMLFilter.__init__(self, params[0], params[1])

