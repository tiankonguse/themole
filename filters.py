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

from queryfilters import *
from htmlfilters import *
from functools import reduce
from exceptions import FilterNotFoundException

class BaseFilterManager:
    def __init__(self, filter_map):
        self.filters = []
        self.filter_map = filter_map

    def active_filters(self):
        return [x[0] for x in self.filters]

    def add_filter(self, name, params):
        if not name in self.filter_map:
            raise FilterNotFoundException()
        self.filters.append((name, self.filter_map[name](params)))

    def remove_filter(self, name):
        self.filters = list(filter(lambda x: x[0] != name, self.filters))

    def apply_filters(self, query):
        return reduce(lambda x,y: y[1].filter(x), self.filters, query)

    def available_filters(self):
        return self.filter_map.keys()

class QueryFilterManager(BaseFilterManager):
    filter_map = {
        'case' : CaseFilter,
        'space2comment' : Spaces2CommentsFilter,
        'mssqlcollation' : SQLServerCollationFilter,
    }
    
    def __init__(self):
        BaseFilterManager.__init__(self, self.filter_map)
    
    def parameters(self, name, args):
        if not name in self.active_filters():
            raise FilterNotFoundException()
        else:
            return self.filters[self.active_filters().index(name)][1].parameters(args)

    def config(self, name, params):
        if not name in self.active_filters():
            raise FilterNotFoundException()
        else:
            self.filters[self.active_filters().index(name)][1].config(params)

class HTMLFilterManager(BaseFilterManager):
    filter_map = {
        'regexrem' : RemoverRegexHTMLFilter,
        'regexrep' : ReplacerRegexHTMLFilter,
    }
    
    def __init__(self):
        BaseFilterManager.__init__(self, self.filter_map)
