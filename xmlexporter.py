
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

from xml.dom import minidom
from base64 import b64encode, b64decode

class XMLExporter:
    
    def export(self, mole_config, schemata, file_name):
        xml_doc = minidom.Document()
        root = xml_doc.createElement("themole")
        xml_doc.appendChild(root)
        
        #Create Mole Config
        config = xml_doc.createElement("config")
        
        #Add all its components
        url = xml_doc.createElement("attribute")
        url.setAttribute("name", "url")
        url.setAttribute("value", b64encode(mole_config.url.encode()).decode())
        config.appendChild(url)
        del url
        needle = xml_doc.createElement("attribute")
        needle.setAttribute("name", "needle")
        needle.setAttribute("value", b64encode(mole_config.needle.encode()).decode())
        config.appendChild(needle)
        del needle
        mode = xml_doc.createElement("attribute")
        mode.setAttribute("name", "mode")
        mode.setAttribute("value", b64encode(mole_config.mode.encode()).decode())
        config.appendChild(mode)
        del mode
        prefix = xml_doc.createElement("attribute")
        prefix.setAttribute("name", "prefix")
        prefix.setAttribute("value", b64encode(mole_config.prefix.encode()).decode())
        config.appendChild(prefix)
        del prefix
        end = xml_doc.createElement("attribute")
        end.setAttribute("name", "end")
        end.setAttribute("value", b64encode(mole_config.end.encode()).decode())
        config.appendChild(end)
        del end
        timeout = xml_doc.createElement("attribute")
        timeout.setAttribute("name", "timeout")
        timeout.setAttribute("value", b64encode(str(mole_config.timeout).encode()).decode())
        config.appendChild(timeout)
        del timeout
        separator = xml_doc.createElement("attribute")
        separator.setAttribute("name", "separator")
        separator.setAttribute("value", b64encode(mole_config.separator.encode()).decode())
        config.appendChild(separator)
        del separator
        comment = xml_doc.createElement("attribute")
        comment.setAttribute("name", "comment")
        comment.setAttribute("value", b64encode(mole_config.comment.encode()).decode())
        config.appendChild(comment)
        del comment
        parenthesis = xml_doc.createElement("attribute")
        parenthesis.setAttribute("name", "parenthesis")
        parenthesis.setAttribute("value", b64encode(str(mole_config.parenthesis).encode()).decode())
        config.appendChild(parenthesis)
        del parenthesis
        dbms_mole = xml_doc.createElement("dbms_mole")
        dbms_mole.setAttribute("type", b64encode(mole_config._dbms_mole.dbms_name().encode()).decode())
        config.appendChild(dbms_mole)
        del dbms_mole
        #Append it to the doc
        root.appendChild(config)
        del config
        
        #Create schema tree
        data_schema = xml_doc.createElement("data_schema")
        
        for (db, tables) in schemata.items():
            #Create the schema entry
            schema_entry = xml_doc.createElement("schema")
            schema_entry.setAttribute("name", b64encode(db.encode()).decode())
            for (table, columns) in tables.items():
                #Create the table entry
                table_entry = xml_doc.createElement("table")
                table_entry.setAttribute("name", b64encode(table.encode()).decode())
                for column in columns:
                    #Create the column entry and store it in the table
                    column_entry = xml_doc.createElement("column")
                    column_entry.setAttribute("name", b64encode(column.encode()).decode())
                    table_entry.appendChild(column_entry)
                #Store the table in the schema
                schema_entry.appendChild(table_entry)
            #Append the schema in the data_schema
            data_schema.appendChild(schema_entry)
        #Append the schema tree to the root.
        root.appendChild(data_schema)
        
        f = open(file_name, "w")
        xml_doc.writexml(f, addindent='    ', newl='\n')
        f.close()
