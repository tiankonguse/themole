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
from moleexceptions import FilterConfigException, FilterCreationError
from queryfilters.base import BaseQueryFilter
from queryfilters import register_query_filter

class CaseFilter(BaseQueryFilter):
    word_delimiters = {' ', '/', '(', ')'}

    def filter(self, query):
        query_list = list(query)
        so_far = ''
        skip_next = False
        for i in range(len(query_list)):
            if query_list[i] in self.word_delimiters:
                if not skip_next:
                    word = query_list[i - len(so_far):i]
                    if ''.join(word).isupper() or ''.join(word).islower():
                        word = [word[i].swapcase() if i % 2 == 1 and not word[i] == 'x' else word[i] for i in range(len(word))]
                        query_list[i - len(so_far):i] = word
                skip_next = (so_far == 'from')
                so_far = ''
            else:
                so_far += query_list[i].lower()
            if not skip_next:
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

class Spaces2NewLineFilter(BaseQueryFilter):
    def filter(self, query):
        return query.replace(' ', '\n')

class SQLServerCollationFilter(BaseQueryFilter):
    def __init__(self, name, params):
        BaseQueryFilter.__init__(self, name, params)
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
            output_manager.error('{0}'.format(ex)).line_break()
        return query

    def config(self, params):
        if len(params) == 0:
            raise FilterConfigException('At least one argument required')
        if params[0] == 'blacklist':
            if len(params) > 1:
                if params[1] == 'add':
                    if len(params) != 3:
                        raise FilterConfigException('Expected argument after "add"')
                    self.blacklist.append(params[2])
                elif params[1] == 'del':
                    if len(params) != 3:
                        raise FilterConfigException('Expected argument after "del"')
                    self.blacklist.remove(params[2])
            else:
                if len(self.blacklist) == 0:
                    output_manager.info('No fields in blacklist.').line_break()
                else:
                    for i in self.blacklist:
                        output_manager.normal(i).line_break()
        elif params[0] == 'collation':
            if len(params) != 2:
                output_manager.normal(self.collation).line_break
            else:
                self.collation = params[1]
        else:
            raise FilterConfigException('Argument ' + params[0] + ' is invalid.')

    def parameters(self, current_params):
        if len(current_params) == 0:
            return ['blacklist', 'collation']
        elif current_params[0] == 'blacklist':
            if len(current_params) == 2:
                return self.blacklist if current_params[1] == 'del' else []
            else:
                return ['add', 'del'] if len(current_params) == 1 else []
        else:
            return []

    def __str__(self):
        return self.name + ' ' + self.collation

class BetweenComparerFilter(BaseQueryFilter):
    def __init__(self, name, params):
        BaseQueryFilter.__init__(self, name, params)
        self.regex = re.compile('([\d]+)[ ]+([<>])[ ]+(\(select [\w\d\(\) _\-\+,\*@\.=]+\))')

    def filter(self, query):
        match = self.regex.search(query)
        if match:
            num, op, select = match.groups()
            preffix = 'not ' if op == '>' else ''
            return query.replace(match.string[match.start():match.end()], preffix + num + ' between 0 and ' + select + '-1 ')
        return query

class ParenthesisFilter(BaseQueryFilter):

    def __init__(self, name, params):
        BaseQueryFilter.__init__(self, name, params)
        self.regex = re.compile('(where|and)[ ]+([\'"\d\w_]+)[ ]*(between|like|[<>=])[ ]*(\(.+\)|[\'"\d\w]+)', re.IGNORECASE)

    def filter(self, query):
        match = self.regex.search(query)
        while match:
            keyword, op1, oper, op2 = match.groups()
            if len(list(filter(lambda x: x == '"' or x == "'", op2))) & 1 == 0:
                op2 = '(' + op2 + ')'
            query = query.replace(match.string[match.start():match.end()], keyword + '(' + op1 + ')' + oper + op2)
            match = self.regex.search(query)
        return query

class NoAsteriskFilter(BaseQueryFilter):
    def filter(self, query):
        return query.replace('*', '1')

class RegexFilter(BaseQueryFilter):
    def __init__(self, name, params):
        BaseQueryFilter.__init__(self, name, params)
        if len(params) != 2:
            raise FilterCreationError('Expected 2 arguments')
        try:
            self.regex = re.compile(params[0], re.IGNORECASE)
            self.replacement = params[1]
        except Exception as ex:
            raise FilterCreationError(str(ex))

    def filter(self, query):
        return self.regex.sub(self.replacement, query)

    def __str__(self):
        return 'regex ' + self.regex.pattern + ' ' + self.replacement


register_query_filter('case', CaseFilter)
register_query_filter('space2comment', Spaces2CommentsFilter)
register_query_filter('space2newline', Spaces2NewLineFilter)
register_query_filter('mssqlcollation', SQLServerCollationFilter)
register_query_filter('between', BetweenComparerFilter)
register_query_filter('parenthesis', ParenthesisFilter)
register_query_filter('noasterisk', NoAsteriskFilter)
register_query_filter('regex', RegexFilter)
