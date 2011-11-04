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

import random, re
from exceptions import *
from queryfilters.base import BaseQueryFilter

class CaseFilter(BaseQueryFilter):
    def filter(self, query):
        query_list = list(query)
        for i in range(len(query_list)):
            # Fix for mysql 0xFFFF syntax. These filters should be
            # applied before converting quoted strings to dbms specific
            # string representation.
            if query_list[i] != 'x' and random.randrange(0, 2) == 0:
                if query_list[i].isupper():
                    query_list[i] = query_list[i].lower()
                else:
                    query_list[i] = query_list[i].upper()
        return ''.join(query_list)


class Spaces2CommentsFilter(BaseQueryFilter):
    def filter(self, query):
        return query.replace(' ', '/**/')

class SQLServerCollationFilter(BaseQueryFilter):
    def __init__(self, params):
        self.cast_match = re.compile('cast\([\w\d_\-@]+ as varchar\([\d]+\)\)')
        self.field_match = re.compile('cast\(([\w\d_\-@]+) as varchar\([\d]+\)\)')
        self.blacklist = []
        self.collation = params[0] if len(params) == 1 else 'DATABASE_DEFAULT'

    def filter(self, query):
        try:
            matches = self.cast_match.findall(query)
            for i in matches:
                field = self.field_match.findall(i)[0]
                if not field in self.blacklist:
                    replaced = i.replace(field, '(' + field + ' COLLATE ' + self.collation + ')')
                    query = query.replace(i, replaced)
        except Exception as ex:
            print(ex)
        return query

    def config(self, params):
        if len(params) == 0:
            raise FilterConfigException('At least one argument required.')
        if params[0] == 'show':
            if len(self.blacklist) == 0:
                print('No fields in blacklist.')
            else:
                for i in self.blacklist:
                    print(i)
        elif params[0] == 'add':
            if len(params) != 2:
                raise FilterConfigException('Expected argument after "add".')
            self.blacklist.append(params[1])
        elif params[0] == 'del':
            if len(params) != 2:
                raise FilterConfigException('Expected argument after "del".')
            self.blacklist.remove(params[1])
        elif params[0] == 'collation':
            if len(params) != 2:
                print(self.collation)
            else:
                self.collation = params[1]
        else:
            raise FilterConfigException('Argument ' + params[0] + ' is invalid.')

    def parameters(self, current_params):
        if len(current_params) == 0:
            return ['add', 'del', 'show', 'collation']
        else:
            return self.blacklist if current_params[0] == 'del' else []
                
                

