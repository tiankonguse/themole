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

try:
    import readline
except ImportError: #Window systems don't have GNU readline
    import pyreadline.windows_readline as readline
    readline.rl.mode.show_all_if_ambiguous = "on"

import re


class CompletionManager:
    def __init__(self, manager, mole):
        self.manager = manager
        self.mole    = mole
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>/?')
        self.parse_regex = re.compile('("[^"]*"|\'[^\']+\')')

    def completer(self, text, state):
        if readline.get_begidx() == 0:
            # means it's the first word on buffer
            return self.generate_commands(text, state)
        else:
            # not the first word on buffer, may be a parameter
            return self.generate_parameters(text, state)

    def generate_parameters(self, text, state):
        if state == 0:
            self.available = []
            self.current = 0
            try:
                line = readline.get_line_buffer()[:readline.get_endidx()].split(' ')
                cmd = self.manager.find(line[0])
            except:
                return 0
            current_params = list(filter(lambda x: len(x.strip()) > 0, line[1:-1] if len(line) > 2 else []))
            if ',' in text:
                text = text.split(',')[-1]
            for i in cmd.parameters(self.mole, current_params):
                if i[:len(text)] == text:
                    self.available.append(i)
            self.available.sort()
            if len(self.available) == 1:
                text = self.available[0]
                self.available = []
                self.current = len(self.available)
                return text + cmd.parameter_separator(current_params)
        return self.get_completion(text, state)

    def generate_commands(self, text, state):
        if state == 0:
            self.available = []
            self.current = 0
            for i in self.manager.commands():
                if i[0:len(text)] == text:
                    self.available.append(i)
            self.available.sort()
            if len(self.available) == 1 and self.available[0] == text:
                self.available = []
                self.current = len(self.available)
                return text + ' '
        return self.get_completion(text, state)

    def get_completion(self, text, state):
        if self.current == len(self.available):
            return None
        else:
            tmp = self.available[self.current]
            self.current += 1
            return tmp + ' '
    
    def smart_parse(self, line):
        output = []
        match = self.parse_regex.search(line)
        start_index = 0
        while match:
            output += self.nice_split(line[start_index:match.start()])
            start_index += match.end()
            output.append(match.groups()[0][1:-1].strip())
            match = self.parse_regex.search(line[start_index:])
        if start_index < len(line):
            output += self.nice_split(line[start_index:])
        return output
    
    def nice_split(self, line):
        return [i for i in line.strip().split(' ') if len(i) > 0]
