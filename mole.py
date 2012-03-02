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

from sys import exit
import getopt, sys
import builtins
import codecs
import signal
import completion

import themole
import commands
from outputmanager import OutputManager

__version__ = '0.3'

def sigint_handler(x, y):
    manager.mole.abort_query()

class Manager:
    def __init__(self, opt_map):
        threads = 4
        if 'threads' in opt_map:
            threads = int(opt_map['threads'])
        self.mole = themole.TheMole(threads=threads)
        self.completer = completion.CompletionManager(cmd_manager, self.mole)
        if 'url' in opt_map:
            try:
                vuln_param = opt_map['vuln_param'] if 'vuln_param' in opt_map else None
                cmd_manager.find('url').execute(self.mole, [opt_map['url'], vuln_param])
            except commands.CommandException as ex:
                output_manager.error('Error while setting URL: {0}'.format(ex)).line_break()
                self.mole.abort_query()
                exit(1)
        if 'needle' in opt_map:
            cmd_manager.find('needle').execute(self.mole, [opt_map['needle']])
        if 'encoding' in opt_map:
            encoding = opt_map['encoding']
            try:
                codecs.lookup(encoding)
            except LookupError:
                output_manager.error('Encoding {0} does not exist.'.format(encoding)).line_break()
                self.mole.threader.stop()
                sys.exit(1)
            self.mole.requester.encoding = encoding

    def start(self):
        while True:
            try:
                signal.signal(signal.SIGINT, signal.default_int_handler)
                try:
                    #line = [i for i in input('#> ').strip().split(' ') if len(i) > 0]
                    line = input('#> ')
                except KeyboardInterrupt:
                    output_manager.line_break()
                    continue

                cmd_name = line.strip().split(' ')
                if len(cmd_name) > 0 and len(cmd_name[0]) > 0:
                    cmd = cmd_manager.find(cmd_name[0])
                    if cmd.requires_smart_parse():
                        line = self.completer.smart_parse(line)
                    else:
                        line = self.completer.nice_split(line)
                    signal.signal(signal.SIGINT, sigint_handler)
                    cmd.execute(self.mole, line[1:] if len(line) > 1 else [])
            except commands.CommandException as ex:
                output_manager.error(str(ex)).line_break()
                if ex.print_usage:
                    output_manager.normal(' Usage: {0}'.format(cmd.usage(line[0]))).line_break()
            except commands.CmdNotFoundException as ex:
                output_manager.error('Error: {0}'.format(ex)).line_break()
            except commands.QuietCommandException:
                pass
            except EOFError:
                output_manager.line_break()
                self.mole.abort_query()
                self.mole.threader.stop()
                exit(0)

def parse_options():
    if '-h' in sys.argv:
        help_()
    options = 'u:n:p:e:t:'
    try:
        args, _ = getopt.getopt(sys.argv[1:], options)
    except getopt.GetoptError as ex:
        print('Invalid parameter({err}).'.format(err=str(ex)))
        exit(1)
    return args

def help_():
    print(' Usage ' + sys.argv[0] + ' [PARAMS]\n')
    print(' The mole v{0} - Automatic SQL Injection exploiter.'.format(__version__))
    print(' Run The mole to begin an interactive session\n')
    print(' Params can be:')
    print('   -u URL: The url which contains a sqli vulnerability.')
    print('   -n NEEDLE: The string which is printed on good queries.')
    print('   -t THREADS: The amount of threads to run. Defaults to 4.')
    print('   -e ENCODING: Use ENCODING to decode data retrieved from the server.')
    print('   -p PARAM: Sets the GET vulnerable param(URL must be provided).')
    exit(0)

info_string = \
r"""                     _____ _           ___  ___      _
                    |_   _| |          |  \/  |     | |
                      | | | |__   ___  | .  . | ___ | | ___
                      | | | '_ \ / _ \ | |\/| |/ _ \| |/ _ \
                      | | | | | |  __/ | |  | | (_) | |  __/
                      \_/ |_| |_|\___| \_|  |_/\___/|_|\___|

 Developed by Nasel(http://www.nasel.com.ar).
 Published under GPLv3.
 Be efficient and have fun!
"""

if __name__ == '__main__':
    options = parse_options()
    option_name_mapper = {
        '-u' : 'url',
        '-n' : 'needle',
        '-t' : 'threads',
        '-p' : 'vuln_param',
        '-e' : 'encoding'
    }
    opt_map = {}
    for i in options:
        opt_map[option_name_mapper[i[0]]] = i[1]

    print(info_string)

    builtins.cmd_manager = commands.CommandManager()
    builtins.manager = Manager(opt_map)
    builtins.output_manager = OutputManager()
    try:
        manager.start()
    except Exception as ex:
        import traceback
        traceback.print_exc(file=sys.stdout)
        output_manager.error('Unexpected error encountered. Please report this bug :D').line_break()
        manager.mole.threader.stop()
