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

import connection, os, output
import themole

class CmdNotFoundException(Exception):
    def __init__(self, message):
        self.message = message

class CommandException(Exception):
    def __init__(self, message):
        self.message = message

class QuietCommandException(Exception):
    pass

class Command:
    def check_initialization(self, mole):
        if not mole.initialized:
            try:
                mole.initialize()
                if not mole.initialized:
                    raise QuietCommandException()
            except themole.MoleAttributeRequired as ex:
                print('Mole error:', ex.message)
                raise CommandException('Mole not ready yet')
            except Exception as ex:
                raise ex
                print(ex)
                raise QuietCommandException()

    def execute(self, mole, params, output_manager):
        pass

    def usage(self, cmd_name):
        return cmd_name

    def parameters(self, mole, current_params):
        return []

    def parameter_separator(self, current_params):
        return ' '

class URLCommand(Command):

    def execute(self, mole, params, output_manager):
        if len(params) < 1:
            if not mole.get_url():
                print('No url defined')
            else:
                print(mole.get_url().replace(mole.wildcard, ''))
        else:
            url = params[0]
            if len(params) == 2:
                mole.set_url(url, params[1])
            else:
                mole.set_url(url)
            mole.restart()

    def usage(self, cmd_name):
        return cmd_name + ' [URL] [PARAM]'

    def parameters(self, mole, current_params):
        if len(current_params) == 1:
            return list(t.split('=', 1)[0] for t in current_params[0].split('&'))
        else:
            return []

class CookieCommand(Command):
    def execute(self, mole, params, output_manager):
        if not mole.requester:
            raise CommandException('URL must be set first.')
        if len(params) == 1:
            mole.requester.headers['Cookie'] = ' '.join(params)
        else:
            print(mole.requester.headers['Cookie'])

    def usage(self, cmd_name):
        return cmd_name + ' [COOKIE]'

class NeedleCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            if not mole.needle:
                print('No needle defined')
            else:
                print(mole.needle)
        else:
            mole.needle = ' '.join(params)

    def usage(self, cmd_name):
        return cmd_name + ' [NEEDLE]'

    def parameters(self, mole, current_params):
        return []

class ClearScreenCommand(Command):
    def execute(self, mole, params, output_manager):
        os.system('clear')

class FetchDataCommand(Command):
    def __init__(self):
        self.cmds = {
                        'schemas' : SchemasCommand(True),
                        'tables'  : TablesCommand(True),
                        'columns' : ColumnsCommand(True),
                    }

    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        if len(params) == 0:
            raise CommandException('At least one parameter is required!')
        self.cmds[params[0]].execute(mole, params[1:], output_manager)

    def usage(self, cmd_name):
        return cmd_name + ' <schemas|tables|columns> [args]'

    def parameters(self, mole, current_params):
        if len(current_params) == 0:
            return ['schemas', 'tables', 'columns']
        else:
            try:
                return self.cmds[current_params[0]].parameters(mole, current_params[1:])
            except KeyError:
                return []


class SchemasCommand(Command):
    def __init__(self, force_fetch=False):
        self.force_fetch = force_fetch

    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        try:
            schemas = mole.get_databases(self.force_fetch)
        except themole.QueryError as ex:
            print('[-]', ex)
            return
        except Exception as ex:
            raise ex
            print('[-]', str(ex))
            return

        output_manager.begin_sequence(['Databases'])
        schemas.sort()
        for i in schemas:
            output_manager.put([i])
        output_manager.end_sequence()

    def parameters(self, mole, current_params):
        return []

class TablesCommand(Command):
    def __init__(self, force_fetch=False):
        self.force_fetch = force_fetch

    def execute(self, mole, params, output_manager):
        if len(params) != 1:
            raise CommandException('Database name required')
        try:
            self.check_initialization(mole)
            tables = mole.get_tables(params[0], self.force_fetch)
        except themole.QueryError as ex:
            print('[-]', ex)
            return
        output_manager.begin_sequence(['Tables'])
        tables.sort()
        for i in tables:
            output_manager.put([i])
        output_manager.end_sequence()

    def usage(self, cmd_name):
        return cmd_name + ' <SCHEMA>'

    def parameters(self, mole, current_params):
        if len(current_params) == 0:
            schemas = mole.poll_databases()
            return schemas if schemas else []
        else:
            return []
            
class FindTablesLikeCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) != 2:
            raise CommandException('Database and table filter required.')
        try:
            self.check_initialization(mole)
            tables = mole.find_tables_like(params[0], "'"  + ' '.join(params[1:]) + "'")
        except themole.QueryError as ex:
            print('[-]', ex)
            return
        output_manager.begin_sequence(['Tables'])
        tables.sort()
        for i in tables:
            output_manager.put([i])
        output_manager.end_sequence()
    
    def usage(self, cmd_name):
        return cmd_name + ' <SCHEMA> <FILTER>'
        
    def parameters(self, mole, current_params):
        if len(current_params) == 0:
            schemas = mole.poll_databases()
            return schemas if schemas else []
        else:
            return []

class ColumnsCommand(Command):
    def __init__(self, force_fetch=False):
        self.force_fetch = force_fetch

    def execute(self, mole, params, output_manager):
        if len(params) != 2:
            raise CommandException('Database name required')
        try:
            self.check_initialization(mole)
            columns = mole.get_columns(params[0], params[1], force_fetch=self.force_fetch)
        except themole.QueryError as ex:
            print('[-]', ex)
            return
        output_manager.begin_sequence(['Columns for table ' + params[1]])
        for i in columns:
            output_manager.put([i])
        output_manager.end_sequence()

    def usage(self, cmd_name):
        return cmd_name + ' <SCHEMA> <TABLE>'

    def parameters(self, mole, current_params):
        if len(current_params) == 0:
            schemas = mole.poll_databases()
            if not schemas:
                return []
            return [i for i in schemas if mole.poll_tables(i) != None]
        elif len(current_params) == 1:
            tables = mole.poll_tables(current_params[0])
            return tables if tables else []
        else:
            return []

class QueryCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) < 3:
            raise CommandException('Database name required')
        try:
            self.check_initialization(mole)
            if len(params) == 4:
                raise CommandException('Expected 3 or at least 5 parameters, got 4.')
            condition = ' '.join(params[4:]) if len(params) > 3 else '1=1'
            result = mole.get_fields(params[0], params[1], params[2].split(','), condition)
        except themole.QueryError as ex:
            print('[-]', ex)
            return
        output_manager.begin_sequence(params[2].split(','))
        for i in result:
            output_manager.put(i)
        output_manager.end_sequence()

    def usage(self, cmd_name):
        return cmd_name + ' <SCHEMA> <TABLE> <COLUMNS> [where <CONDITION>]'

    def parameters(self, mole, current_params):
        if len(current_params) == 0:
            schemas = mole.poll_databases()
            if not schemas:
                return []
            return schemas
        elif len(current_params) == 1:
            tables = mole.poll_tables(current_params[0])
            if not tables:
                return []
            return tables
        elif len(current_params) == 2:
            columns = mole.poll_columns(current_params[0], current_params[1])
            return columns if columns else []
        elif len(current_params) == 3 :
            return ['where']
        else:
            columns = mole.poll_columns(current_params[0], current_params[1])
            return columns if columns else []

    def parameter_separator(self, current_params):
        return ' ' if len(current_params) <= 1 else ''

class DBInfoCommand(Command):
    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        try:
            info = mole.get_dbinfo()
        except themole.QueryError:
            print('[-] There was an error with the query.')
            return
        print(" User:     ", info[0])
        print(" Version:  ", info[1])
        print(" Database: ", info[2])

    def parameters(self, mole, current_params):
        return []

class BruteforceTablesCommand(Command):
    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        if len(params) < 2:
            raise CommandException("DB name and table names to bruteforce required.")
        else:
            mole.brute_force_tables(params[0], params[1:])

    def usage(self, cmd_name):
        return cmd_name + ' DB TABLE1 [TABLE2 [...]]'

class BruteforceUserTableCommand(Command):
    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        if len(params) == 0:
            raise CommandException("DB name expected as argument.")
        else:
            mole.brute_force_users_tables(params[0])

    def usage(self, cmd_name):
        return cmd_name + ' <SCHEMA>'

class ExitCommand(Command):
    def execute(self, mole, params, output_manager):
        mole.abort_query()
        mole.threader.stop()
        exit(0)

class QueryModeCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            print(mole.mode)
        else:
            if not params[0] in ['union', 'blind']:
                raise CommandException('Invalid query mode.')
            mole.set_mode(params[0])

    def parameters(self, mole, current_params):
        return ['union', 'blind'] if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <union|blind>'

class PrefixCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            print(mole.prefix)
        else:
            if params[0].startswith('"') or params[0].startswith('\''):
                mole.prefix = ' '.join(params)
            else:
                mole.prefix = ' ' + ' '.join(params)

    def usage(self, cmd_name):
        return cmd_name + ' [PREFIX]'

class SuffixCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            print(mole.end)
        else:
            if params[0].startswith('"') or params[0].startswith('\''):
                mole.end = ' '.join(params)
            else:
                mole.end = ' ' + ' '.join(params)

    def usage(self, cmd_name):
        return cmd_name + ' [SUFFIX]'

class TimeoutCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            print(mole.timeout)
        else:
            mole.timeout = float(params[0])
            if mole.requester:
                mole.requester.timeout = mole.timeout

    def usage(self, cmd_name):
        return cmd_name + ' [TIMEOUT]'

class VerboseCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            print('on' if mole.verbose else 'off')
        else:
            if not params[0] in ['on', 'off']:
                raise CommandException('Invalid parameter.')
            mole.verbose = True if params[0] == 'on' else False

    def parameters(self, mole, current_params):
        return ['on', 'off'] if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <on|off>'

class OutputCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) != 1:
            raise CommandException('Expected output manager name as parameter')
        if params[0] not in ['pretty', 'plain']:
            raise CommandException('Unknown output manager.')
        if params[0] == 'pretty':
            new_output = output.PrettyOutputManager()
        else:
            new_output = output.PlainOutputManager()
        manager.output = new_output

    def parameters(self, mole, current_params):
        return ['pretty', 'plain'] if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <pretty(default)|plain>'

class UsageCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) == 0:
            raise CommandException('Command required as argument')
        else:
            cmd = cmd_manager.find(params[0])
            print(' ' + cmd.usage(params[0]))


    def parameters(self, mole, current_params):
        return cmd_manager.cmds.keys() if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <on|off>'

class ExportCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) != 2:
            raise CommandException('Expected type and filename as parameter')
        if params[0] not in ['xml']:
            raise CommandException('Unknown export format.')
        mole.export_xml(params[1])

    def parameters(self, mole, current_params):
        return ['xml'] if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <format> <output_filename>'

class ImportCommand(Command):
    def execute(self, mole, params, output_manager):
        if len(params) != 2:
            raise CommandException('Expected type and filename as parameter')
        if params[0] not in ['xml']:
            raise CommandException('Unknown import format.')
        mole.import_xml(params[1])

    def parameters(self, mole, current_params):
        return ['xml'] if len(current_params) == 0 else []

    def usage(self, cmd_name):
        return cmd_name + ' <format> <input_filename>'


class ReadFileCommand(Command):
    def execute(self, mole, params, output_manager):
        self.check_initialization(mole)
        if len(params) != 1:
            raise CommandException('Expected filename as parameter')
        data = mole.read_file(params[0])
        if len(data) == 0:
            print('[-] Error reading file or file is empty.')
        else:
            print(data)

    def parameters(self, mole, current_params):
        return []

    def usage(self, cmd_name):
        return cmd_name + ' <filename>'

class CommandManager:
    def __init__(self):
        self.cmds = { 'find_tables' : BruteforceTablesCommand(),
                      'find_tables_like' : FindTablesLikeCommand(),
                      'find_users_table'  : BruteforceUserTableCommand(),
                      'clear'    : ClearScreenCommand(),
                      'columns'  : ColumnsCommand(),
                      'cookie'   : CookieCommand(),
                      'dbinfo'   : DBInfoCommand(),
                      'exit'     : ExitCommand(),
                      'export'   : ExportCommand(),
                      'fetch'    : FetchDataCommand(),
                      'import'   : ImportCommand(),
                      'mode'     : QueryModeCommand(),
                      'needle'   : NeedleCommand(),
                      'output'   : OutputCommand(),
                      'prefix'   : PrefixCommand(),
                      'query'    : QueryCommand(),
                      'readfile' : ReadFileCommand(),
                      'schemas'  : SchemasCommand(),
                      'suffix'   : SuffixCommand(),
                      'tables'   : TablesCommand(),
                      'timeout'  : TimeoutCommand(),
                      'url'      : URLCommand(),
                      'usage'    : UsageCommand(),
                      'verbose'  : VerboseCommand(),
                    }

    def find(self, cmd):
        if cmd in self.cmds:
            return self.cmds[cmd]
        else:
            raise CmdNotFoundException(cmd + ' is not a valid command')

    def commands(self):
        return self.cmds.keys()
