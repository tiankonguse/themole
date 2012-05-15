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

import os
import sys

from functools import reduce
from moleexceptions import FilterNotFoundException
import queryfilters, responsefilters, requestfilters

class BaseFilterManager:
    def __init__(self, import_dir):
        full_import_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), import_dir)
        self.filters = []
        self.filter_map = {}
        classes = [x[:-3] for x in os.listdir(full_import_dir) if not x.startswith('__') and x.endswith('.py')]
        for c in classes:
            __import__(import_dir + '.' + c, globals(), locals())

    def active_filters(self):
        return [x[0] for x in self.filters]

    def active_filters_to_string(self):
        return [str(x[1]) for x in self.filters]

    def add_filter(self, name, params):
        if not name in self.filter_map:
            raise FilterNotFoundException()
        filter_object = self.filter_map[name](name, params)
        self.filters.append((name, filter_object))
        return filter_object

    def remove_filter(self, name):
        self.filters = list(filter(lambda x: x[0] != name, self.filters))

    def apply_filters(self, query):
        return reduce(lambda x, y: y[1].filter_(x), self.filters, query)

    def available_filters(self):
        return self.filter_map.keys()

    def register_filter(self, name, filter_class):
        self.filter_map[name] = filter_class

class QueryFilterManager(BaseFilterManager):
    def __init__(self):
        queryfilters.register_query_filter = self.register_filter
        BaseFilterManager.__init__(self, 'queryfilters')

    def parameters(self, name, args):
        if not name in self.active_filters():
            raise FilterNotFoundException()
        else:
            return self.filters[self.active_filters().index(name)][1].parameters(args)

    def config_parameters(self, name):
        if not name in self.active_filters():
            raise FilterNotFoundException()
        else:
            return self.filters[self.active_filters().index(name)][1].configuration_parameters()

    def config(self, name, params):
        if not name in self.active_filters():
            raise FilterNotFoundException()
        else:
            self.filters[self.active_filters().index(name)][1].config(params)

class ResponseFilterManager(BaseFilterManager):
    def __init__(self):
        responsefilters.register_response_filter = self.register_filter
        BaseFilterManager.__init__(self, 'responsefilters')

class RequestFilterManager(BaseFilterManager):
    def __init__(self):
        requestfilters.register_request_filter = self.register_filter
        BaseFilterManager.__init__(self, 'requestfilters')
