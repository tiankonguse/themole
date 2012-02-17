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

    def __init__(self):
        self.lock = threading.Lock()
        self.last_line_length = 0
        self.result_output = 'pretty'
        self.echo_output = True

    def normal(self, string):
        if self.echo_output:
            with self.lock:
                self._erase_line()
                self.last_line_length = len(string)
                sys.stdout.write(string)
                sys.stdout.flush()
        return self

    def advance(self, string):
        if self.echo_output:
            with self.lock:
                self._erase_line()
                string = '[+] ' + string
                self.last_line_length = len(string)
                sys.stdout.write(string)
                sys.stdout.flush()
        return self


    def info(self, string):
        if self.echo_output:
            with self.lock:
                self._erase_line()
                string = '[i] ' + string
                self.last_line_length = len(string)
                sys.stdout.write(string)
                sys.stdout.flush()
        return self

    def debug(self, string):
        if self.echo_output:
            with self.lock:
                self._erase_line()
                string = '[d] ' + string
                self.last_line_length = len(string)
                sys.stdout.write(string)
                sys.stdout.flush()
        return self

    def error(self, string):
        if self.echo_output:
            with self.lock:
                self._erase_line()
                string = '[-] ' + string
                self.last_line_length = len(string)
                sys.stdout.write(string)
                sys.stdout.flush()
        return self

    def line_break(self):
        if self.echo_output:
            sys.stdout.write('\n')
            sys.stdout.flush()
        return self

    def results_output(self, headers):
        if self.result_output == 'plain':
            return PlainResultsOutput(self, headers)
        else:
            return PrettyResultsOutput(self, headers)

    def blind_output(self, length):
        return BlindSQLIOutput(self, length)

    def row_done_counter(self, total):
        return RowDoneCounter(self, total)

    def _erase_line(self):
        sys.stdout.write('\r' + ' ' * self.last_line_length + '\r')
        return self


class BlindSQLIOutput:
    def __init__(self, output_manager, length):
        self.om = output_manager
        self.word = [' ' for _ in range(length)]
        self.om.normal(''.join(self.word))

    def set(self, char, index):
        self.word[index] = char
        self.om.normal(''.join(self.word))

    def finish(self):
        self.om.line_break()

class ResultsOutput:
    def __init__(self, output_manager, header):
        self.om = output_manager
        self.results = []
        self.headers = header

    def put(self, string):
        self.results.append(string)

    def end_sequence(self):
        pass

class PrettyResultsOutput(ResultsOutput):
    def __init__(self, output_manager, header):
        ResultsOutput.__init__(self, output_manager, header)
        self.lengths = list(map(len, header))

    def end_sequence(self):
        for i in self.results:
            for j in range(len(i)):
                self.lengths[j] = max(len(i[j]), self.lengths[j])
        total_len = sum(self.lengths)
        self.om.normal('+' + '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1) + '+').line_break()
        line = ''
        for i in range(len(self.headers)):
            line += '| ' + self.headers[i] + ' ' * (self.lengths[i] - len(self.headers[i]) + 1)
        self.om.normal(line + '|').line_break()
        self.om.normal('+' + '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1) + '+').line_break()
        for i in self.results:
            line = ''
            for j in range(len(i)):
                line += '| ' + i[j] + ' ' * (self.lengths[j] - len(i[j]) + 1)
            self.om.normal(line + '|').line_break()
        self.om.normal('+' + '-' * (total_len + 2 * len(self.lengths) + len(self.lengths) - 1) + '+').line_break()

class PlainResultsOutput(ResultsOutput):

    def end_sequence(self):
        self.om.normal(','.join(self.headers)).line_break()
        self.om.normal('=' * len(','.join(self.headers))).line_break()
        for result in self.results:
            self.om.normal(','.join(result)).line_break()

class RowDoneCounter:

    def __init__(self, output_manager, total):
        self.__om = output_manager
        self.__value = 0
        self.__total = total
        self.__lock = threading.Lock()
        self.__om.info('Dumped {0}/{1} rows.'.format(self.__value, self.__total))


    def increment(self):
        with self.__lock:
            self.__value += 1
            self.__om.info('Dumped {0}/{1} rows.'.format(self.__value, self.__total))

