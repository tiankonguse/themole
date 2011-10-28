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

import sys
import threading

class OutputManager:
    def put(self, string):
        pass

    def begin_sequence(self, string):
        pass

    def end_sequence(self):
        pass


class PrettyOutputManager(OutputManager):
    def __init__(self):
        self.results = []
        self.lengths = []
        self.headers = ''
        self.current_index = 1

    def put(self, string):
        sys.stdout.write('\r[i] ' + str(self.current_index) + '/' + str(len(self.lengths)))
        sys.stdout.flush()
        self.results.append(string)

    def begin_sequence(self, header):
        self.current_index = 1
        self.results = []
        self.headers = header
        self.lengths = list(map(len, header))

    def end_sequence(self):
        for i in self.results:
            for j in range(len(i)):
                self.lengths[j] = max(len(i[j]), self.lengths[j])
        total_len = sum(self.lengths)
        print('\r','+', '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1), '+', sep='')
        line = ''
        for i in range(len(self.headers)):
            line += '| ' + self.headers[i] + ' ' * (self.lengths[i] - len(self.headers[i]) + 1)
        print(line + '|')
        print('+', '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1), '+', sep='')
        for i in self.results:
            line = ''
            for j in range(len(i)):
                line += '| ' + i[j] + ' ' * (self.lengths[j] - len(i[j]) + 1)
            print(line + '|')
        print('+', '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1), '+', sep='')

class PlainOutputManager(OutputManager):
    def begin_sequence(self, string):
        string[-1] = string[-1] + ': '
        self.put(string)

    def put(self, string):
        print(', '. join(string))


class BlindSQLIOutput:
    def __init__(self, length):
        self.word = [' ' for i in range(length)]
        sys.stdout.write(' ' * length)
        sys.stdout.flush()

    def set(self, char, index):
        self.word[index] = char
        sys.stdout.write('\r' + ''.join(self.word))
        sys.stdout.flush()

    def finish(self):
        print('')

class RowDoneCounter:

    def __init__(self, total):
        self.__value = 0
        self.__total = total
        self.__lock = threading.Lock()

    def increment(self):
        with self.__lock:
            self.__value += 1
            print('\r[*] Dumped {0}/{1} rows.'.format(self.__value, self.__total), end='')
