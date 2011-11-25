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

import themole
import completion
import output
import signal
import builtins
import commands
import getopt, sys
import traceback

VERSION = '0.2.6'

def sigint_handler(x, y):
    manager.mole.abort_query()

class Manager:
    def __init__(self, opt_map):
        threads = 4
        if 'threads' in opt_map:
            threads = int(opt_map['threads'])
        self.mole = themole.TheMole(threads=threads)
        self.completer   = completion.CompletionManager(cmd_manager, self.mole)
        self.output      = output.PrettyOutputManager()
        if 'url' in opt_map:
            try:
                vuln_param = opt_map['vuln_param'] if 'vuln_param' in opt_map else None
                cmd_manager.find('url').execute(self.mole, [opt_map['url'], vuln_param], self.output)
            except commands.CommandException as ex:
                print('[-] Error while setting URL:', ex)
                self.mole.abort_query()
                exit(1)
        if 'needle' in opt_map:
            cmd_manager.find('needle').execute(self.mole, [opt_map['needle']], self.output)

    def start(self):
        while True:
            try:
                signal.signal(signal.SIGINT, signal.default_int_handler)
                try:
                    line = [i for i in input('#> ').strip().split(' ') if len(i) > 0]
                except KeyboardInterrupt:
                    print('')
                    continue
                signal.signal(signal.SIGINT, sigint_handler)
                if len(line) != 0:
                    cmd = cmd_manager.find(line[0])
                    cmd.execute(self.mole, line[1:] if len(line) > 1 else [], self.output)
            except commands.CommandException as ex:
                print('[-]', ex)
                if ex.print_usage:
                    print(' Usage:', cmd.usage(line[0]))
            except commands.CmdNotFoundException as ex:
                print(' Error:', ex)
            except commands.QuietCommandException:
                pass
            except EOFError:
                print('')
                self.mole.abort_query()
                self.mole.threader.stop()
                exit(0)

def parse_options():
    if '-h' in sys.argv:
        help()
    options = 'u:n:t:p:'
    try:
        args, extra = getopt.getopt(sys.argv[1:], options)
    except getopt.GetoptError as ex:
        print('Invalid parameter({err}).'.format(err=str(ex)))
        exit(1)
    return args

def help():
    print(' Usage ' + sys.argv[0] + ' [PARAMS]\n')
    print(' The mole v{0} - Automatic SQL Injection exploiter.'.format(VERSION))
    print(' Run The mole to begin an interactive session\n')
    print(' Params can be:')
    print('   -u URL: The url which contains a sqli vulnerability.')
    print('   -n NEEDLE: The string which is printed on good queries.')
    print('   -t THREADS: The amount of threads to run. Defaults to 4.')
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
    }
    opt_map = {}
    for i in options:
        opt_map[option_name_mapper[i[0]]] = i[1]

    print(info_string)

    builtins.cmd_manager = commands.CommandManager()
    builtins.manager = Manager(opt_map)
    try:
        manager.start()
    except Exception as ex:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        print('[-] Unexpected error encountered. Please report this bug :D')
        manager.mole.threader.stop()
