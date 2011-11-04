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

class DatabaseDump():
    def __init__(self):
        self.db_map = {}
    
    def add_db(self, db):
        self.db_map[db] = {}
    
    def add_table(self, db, table):
        if not db in self.db_map:
            self.add_db(db)
        self.db_map[db][table] = set()
    
    def add_column(self, db, table, column):
        if not db in self.db_map:
            self.add_db(db)
        if not table in self.db_map[db]:
            self.add_table(db, table)
        self.db_map[db][table].add(column)
        
    
