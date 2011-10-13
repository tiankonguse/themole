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
    separator = '[_SQL_]'
    
    def execute(self, mole, params, output_manager):
        if len(params) != 1:
            if not mole.url:
                print('No url defined')
            else:
                print(mole.requester.url + '?' + mole.url.replace(URLCommand.separator, ''))
        else:
            url = params[0]
            if not '?' in url:
                raise CommandException('URL requires GET parameters')
            url = url.split('?')
            mole.restart()
            mole.requester = connection.HttpRequester(url[0], timeout=mole.timeout)
            mole.url = url[1] + URLCommand.separator
            mole.wildcard = URLCommand.separator
    
    def usage(self, cmd_name):
        return cmd_name + ' [URL]'
        
    def parameters(self, mole, current_params):
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

class CommandManager:
    def __init__(self):
        self.cmds = { 'clear'    : ClearScreenCommand(),
                      'columns'  : ColumnsCommand(),
                      'cookie'   : CookieCommand(),
                      'dbinfo'   : DBInfoCommand(),
                      'exit'     : ExitCommand(),
                      'fetch'    : FetchDataCommand(),
                      'mode'     : QueryModeCommand(),
                      'needle'   : NeedleCommand(),
                      'output'   : OutputCommand(),
                      'prefix'   : PrefixCommand(),
                      'query'    : QueryCommand(),
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
