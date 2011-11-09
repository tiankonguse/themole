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

from output import BlindSQLIOutput, RowDoneCounter
from exceptions import *

class BlindDataDumper:

    name = 'BlindDataDumper'

    def get_databases(self, mole, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.schema_blind_count_query(x, y)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.schema_blind_len_query(y, z, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.schema_blind_data_query(x, y, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_tables(self, mole, db, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.table_blind_count_query(x, y, db=db)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.table_blind_len_query(y, z, db=db, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.table_blind_data_query(x, y, db=db, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_columns(self, mole, db, table, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.columns_blind_count_query(x, y, db=db, table=table)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.columns_blind_len_query(y, z, db=db, table=table, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.columns_blind_data_query(x, y, db=db, table=table, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_fields(self, mole, db, table, fields, where, injectable_field, start=0, limit=0x7fffffff):
        count_fun = lambda x,y: mole._dbms_mole.fields_blind_count_query(x, y, db=db, table=table, where=where)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.fields_blind_len_query(y, z, fields=fields, db=db, table=table, offset=x, where=where)
        query_fun = lambda x,y,z: mole._dbms_mole.fields_blind_data_query(x, y, fields=fields, db=db, table=table, offset=z, where=where)
        return self._blind_query(mole, count_fun, length_fun, query_fun, start=start, limit=limit)

    def get_dbinfo(self, mole, injectable_field):
        count_fun = None
        length_fun = lambda x: lambda y,z: mole._dbms_mole.dbinfo_blind_len_query(y, z)
        query_fun = lambda x,y,z: mole._dbms_mole.dbinfo_blind_data_query(x, y)

        data = self._blind_query(mole, count_fun, length_fun, query_fun, row_count=1)
        if len(data) != 1 or len(data[0]) != 3:
            raise QueryError('Query did not generate any output.')
        return [data[0][0], data[0][1], data[0][2]]

    def find_tables_like(self, mole, db, table_filter, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.tables_like_blind_count_query(x, y, db=db, table_filter=table_filter)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.tables_like_blind_len_query(y, z, db=db, table_filter=table_filter, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.tables_like_blind_data_query(x, y, db=db, table_filter=table_filter, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def table_exists(self, mole, db, table, injectable_field):
        try:
            req = mole.make_request(mole._dbms_mole.fields_blind_count_query('>', 100000000, db=db, table=table))
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        return mole.analyser.is_valid(req)

    def read_file(self, mole, filename, injectable_field):
        return 'Not implemented.'

    def _blind_query(self, mole, count_fun, length_fun, query_fun, limit=0x7fffffff, start=0, row_count=None):
        mole.stop_query = False
        if count_fun is None:
            count = row_count
        else:
            count = self._generic_blind_len(
                mole,
                count_fun,
                lambda x: '\rTrying count: ' + str(x),
                lambda x: '\rAt most count: ' + str(x)
            )
            count = min(count, limit+start)
            print('\r[+] Found row count:', count)
        results = []
        for row in range(start, count):
            if mole.stop_query:
                return results
            length = self._generic_blind_len(
                mole,
                length_fun(row),
                lambda x: '\rTrying length: ' + str(x),
                lambda x: '\rAt most length: ' + str(x)
            )
            print('\r[+] Guessed length:', length)
            output=''
            if mole.stop_query:
                return results
            sqli_output = BlindSQLIOutput(length)
            gen_query_item = lambda i: self._blind_query_character(mole, query_fun, i, row, sqli_output)
            output = ''.join(mole.threader.execute(length, gen_query_item))
            if not mole.stop_query:
                sqli_output.finish()
            else:
                print('')
            results.append(output.split(mole._dbms_mole.blind_field_delimiter()))
        return results

    def _generic_blind_len(self, mole, count_fun, trying_msg, max_msg):
        length = 0
        last = 1
        while True and not mole.stop_query:
            try:
                req = mole.make_request(count_fun('>', last))
            except ConnectionException as ex:
                raise QueryError('Connection Error: (' + str(ex) + ')')
            print(trying_msg(last), end='')
            if mole.needle in req:
                break;
            last *= 2
        print(max_msg(str(last)), end='')
        pri = last // 2
        while pri < last:
            if mole.stop_query:
                return pri
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            try:
                req = mole.make_request(count_fun('<', medio - 1))
            except ConnectionException as ex:
                raise QueryError('Connection Error: (' + str(ex) + ')')
            if mole.needle in req:
                pri = medio
            else:
                last = medio - 1
        return pri

    def _blind_query_character(self, mole, query_fun, index, offset, output=None):
        pri   = ord(' ')
        last  = 126
        index = index + 1
        while True:
            if mole.stop_query:
                return None
            medio = (pri + last)//2
            try:
                response = mole.requester.request(
                            mole.generate_url(query_fun(index, medio, offset))
                           )
            except ConnectionException as ex:
                raise QueryError('Connection Error: (' + str(ex) + ')')
            if mole.needle in response:
                pri = medio+1
            else:
                last = medio
            if medio == last - 1:
                output.set(chr(medio+1), index - 1)
                return chr(medio+1)
            else:
                if pri == last:
                    output.set(chr(medio), index - 1)
                    return chr(medio)
                else:
                    output.set(chr(medio), index - 1)

class StringUnionDataDumper:

    name = 'StringUnionDataDumper'

    def get_databases(self, mole, injectable_field):
        count_query = mole._dbms_mole.schema_count_query(injectable_field)
        query_gen =  lambda x: mole._dbms_mole.schema_query(injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_tables(self, mole, db, injectable_field):
        count_query = mole._dbms_mole.table_count_query(db, injectable_field)
        query_gen = lambda x: mole._dbms_mole.table_query(db, injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_columns(self, mole, db, table, injectable_field):
        count_query = mole._dbms_mole.columns_count_query(db, table, injectable_field)
        query_gen = lambda x: mole._dbms_mole.columns_query(db, table, injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_fields(self, mole, db, table, fields, where, injectable_field, start=0, limit=0x7fffffff):
        count_query = mole._dbms_mole.fields_count_query(db, table, injectable_field, where=where)
        query_gen = lambda x: mole._dbms_mole.fields_query(db, table, fields, injectable_field, offset=x+start, where=where)
        return self._generic_query(mole, count_query, query_gen, lambda x: x, start=start, limit=limit)

    def get_dbinfo(self, mole, injectable_field):
        query = mole._dbms_mole.dbinfo_query(injectable_field)
        req = mole.make_request(query)
        try:
            data = mole._dbms_mole.parse_results(req)
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        if not data or len(data) != 3:
            raise QueryError('Query did not generate any output.')
        else:
            return data

    def find_tables_like(self, mole, db, table_filter, injectable_field):
        count_query = mole._dbms_mole.tables_like_count_query(db, injectable_field, table_filter)
        query_gen = lambda x: mole._dbms_mole.tables_like_query(db, injectable_field, table_filter, x)
        return self._generic_query(mole, count_query, query_gen)

    def table_exists(self, mole, db, table, injectable_field):
        req = mole.make_request(mole._dbms_mole.fields_count_query(db, table, injectable_field))
        return not mole._dbms_mole.parse_results(req) is None

    def read_file(self, mole, filename, injectable_field):
        query = mole._dbms_mole.read_file_query(filename, injectable_field)
        try:
            req = mole.make_request(query)
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        result = mole._dbms_mole.parse_results(req)
        return result[0] if not result is None else ''

    def _generic_query(self, mole,
                             count_query,
                             query_generator,
                             result_parser = lambda x: x[0],
                             start=0, limit=0x7fffffff):
        try:
            req = mole.make_request(count_query)
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        result = mole._dbms_mole.parse_results(req)
        if not result or len(result) != 1:
            raise QueryError('Count query failed.')
        else:
            count = int(result[0])
            if count == 0:
                return []
            count = min(count, limit+start)
            if start >= count:
                return []
            print('\r[+] Rows: ' + str(count))
            rows_done = RowDoneCounter(count)
            dump_result = []
            mole.stop_query = False
            gen_query_item = lambda i: self._generic_query_item(mole, query_generator, i, rows_done, result_parser)
            dump_result = mole.threader.execute(count-start, gen_query_item)
            print('') #Print a new line to show the results in the next line
            dump_result.sort()
            return dump_result

    def _generic_query_item(self, mole,
                                  query_generator,
                                  offset,
                                  rows_done_counter,
                                  result_parser = lambda x: x[0]):
        if mole.stop_query:
            return None
        try:
            req = mole.make_request(query_generator(offset))
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        result = mole._dbms_mole.parse_results(req)
        if not result or len(result) < 1:
            raise QueryError('Query did not generate any output.')
        else:
            rows_done_counter.increment()
            return result_parser(result)

class IntegerUnionDataDumper:

    name = 'IntegerUnionDataDumper'

    def get_databases(self, mole, injectable_field):
        count_query = mole._dbms_mole.schema_integer_count_query(injectable_field)
        length_query = lambda x: mole._dbms_mole.schema_integer_len_query(injectable_field,
                                                                          offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.schema_integer_query(index,
                                                                               injectable_field,
                                                                               offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_tables(self, mole, db, injectable_field):
        count_query = mole._dbms_mole.table_integer_count_query(db,
                                                                injectable_field)
        length_query = lambda x: mole._dbms_mole.table_integer_len_query(db,
                                                                         injectable_field,
                                                                         offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.table_integer_query(index,
                                                                              db,
                                                                              injectable_field,
                                                                              offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_columns(self, mole, db, table, injectable_field):
        count_query = mole._dbms_mole.columns_integer_count_query(db,
                                                                  table,
                                                                  injectable_field)
        length_query = lambda x: mole._dbms_mole.columns_integer_len_query(db,
                                                                           table,
                                                                           injectable_field,
                                                                           offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.columns_integer_query(index,
                                                                                db,
                                                                                table,
                                                                                injectable_field,
                                                                                offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_fields(self, mole, db, table, fields, where, injectable_field, start=0, limit=0x7fffffff):
        count_query = mole._dbms_mole.fields_integer_count_query(db,
                                                                 table,
                                                                 injectable_field,
                                                                 where=where)
        length_query = lambda x: mole._dbms_mole.fields_integer_len_query(db,
                                                                          table,
                                                                          fields,
                                                                          injectable_field,
                                                                          offset=x,
                                                                          where=where)
        query_gen = lambda index, offset: mole._dbms_mole.fields_integer_query(index,
                                                                               db,
                                                                               table,
                                                                               fields,
                                                                               injectable_field,
                                                                               offset=offset,
                                                                               where=where)
        data = self._generic_integer_query(mole, count_query, length_query, query_gen, start=start, limit=limit)

        return map(lambda x: x.split(mole._dbms_mole.blind_field_delimiter()), data)

    def get_dbinfo(self, mole, injectable_field):
        mole.stop_query = False
        query = mole._dbms_mole.dbinfo_integer_len_query(injectable_field)
        try:
            req = mole.make_request(query)
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        length = mole._dbms_mole.parse_results(req)
        length = int(length[0])

        sqli_output = BlindSQLIOutput(length)
        query_gen = lambda index,offset: mole._dbms_mole.dbinfo_integer_query(index,
                                                                              injectable_field)
        query_item_gen = lambda x: self._generic_integer_query_item(mole,
                                                                    query_gen,
                                                                    x,
                                                                    0,
                                                                    sqli_output)
        data = ''.join(mole.threader.execute(length, query_item_gen))
        sqli_output.finish()
        data = data.split(mole._dbms_mole.blind_field_delimiter())
        if not data or len(data) != 3:
            raise QueryError('Query did not generate any output.')
        else:
            return data

    def find_tables_like(self, mole, db, table_filter, injectable_field):
        count_query = mole._dbms_mole.tables_like_integer_count_query(db, injectable_field, table_filter)
        query_gen = lambda index,offset: mole._dbms_mole.tables_like_integer_query(index,
                                                                                   db,
                                                                                   injectable_field,
                                                                                   table_filter=table_filter,
                                                                                   offset=offset)
        length_query = lambda x: mole._dbms_mole.tables_like_integer_len_query(db,
                                                                          injectable_field,
                                                                          offset=x,
                                                                          table_filter=table_filter)
        data = self._generic_integer_query(mole, count_query, length_query, query_gen)
        return data

    def table_exists(self, mole, db, table, injectable_field):
        try:
            req = mole.make_request(mole._dbms_mole.fields_integer_count_query(db, table, injectable_field))
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        return not mole._dbms_mole.parse_results(req) is None

    def read_file(self, mole, filename, injectable_field):
        mole.stop_query = False
        query = mole._dbms_mole.read_file_integer_len_query(filename, injectable_field)
        try:
            req = mole.make_request(query)
        except ConnectionException as es:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        length = mole._dbms_mole.parse_results(req)
        if length is None or len(length) == 0:
            return ''
        length = int(length[0])

        sqli_output = BlindSQLIOutput(length)
        query_gen = lambda index,offset: mole._dbms_mole.read_file_integer_query(index,
                                                                              filename,
                                                                              injectable_field)
        query_item_gen = lambda x: self._generic_integer_query_item(mole,
                                                                    query_gen,
                                                                    x,
                                                                    0,
                                                                    sqli_output)
        data = ''.join(mole.threader.execute(length, query_item_gen))
        sqli_output.finish()
        data = data.split(mole._dbms_mole.blind_field_delimiter())
        if not data or len(data) != 1:
            raise QueryError('Query did not generate any output.')
        else:
            return data[0]

    def _generic_integer_query(self, mole,
                                     count_query,
                                     length_query,
                                     query_generator,
                                     result_parser = lambda x: x[0],
                                     start=0, limit=0x7fffffff):
        try:
            req = mole.make_request(count_query)
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        result = mole._dbms_mole.parse_results(req)
        if not result:
            raise QueryError('Count query failed.')
        else:
            count = int(result[0])
            if count == 0:
                return []
            count = min(count, limit+start)
            print('\r[+] Rows:', count)
            dump_result = []
            mole.stop_query = False
            for i in range(start,count):
                if mole.stop_query:
                    break
                try:
                    req = mole.requester.request(mole.generate_url(length_query(i)))
                except ConnectionException as ex:
                    raise QueryError('Connection Error: (' + str(ex) + ')')
                length = mole._dbms_mole.parse_results(req)
                if length is None:
                    break
                length = int(length[0])
                sqli_output = BlindSQLIOutput(length)
                gen_query_item = lambda x: self._generic_integer_query_item(mole, query_generator, x, i, sqli_output)
                dump_result.append(''.join(mole.threader.execute(length, gen_query_item)))
                if not mole.stop_query:
                    sqli_output.finish()
            dump_result.sort()
            return dump_result

    def _generic_integer_query_item(self, mole, query_generator, index, offset, sqli_output):
        if mole.stop_query:
            return None
        try:
            req = mole.make_request(query_generator(index+1, offset=offset))
        except ConnectionException as ex:
            raise QueryError('Connection Error: (' + str(ex) + ')')
        result = mole._dbms_mole.parse_results(req)
        if not result or len(result) < 1:
            raise QueryError('Query did not generate any output.')
        else:
            result = chr(int(result[0]))
            sqli_output.set(result, index)
            return result

classes_dict = {
    'BlindDataDumper' : BlindDataDumper,
    'StringUnionDataDumper' : StringUnionDataDumper,
    'IntegerUnionDataDumper' : IntegerUnionDataDumper,
}
