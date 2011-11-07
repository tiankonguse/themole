
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

from pickle import dumps, loads

from base64 import b64encode, b64decode
import binascii
from lxml import etree

from dbmsmoles.dbmsmole import FingerBase
from datadumper import classes_dict as datadumper_classes
from domanalyser import DomAnalyser
from exceptions import *

dtd = """<!DOCTYPE themole [
<!ELEMENT themole (config, data_schema)>
<!ELEMENT config (mole_config, dbms_mole, data_dumper, connection)>
<!ELEMENT mole_config EMPTY>
<!ATTLIST mole_config comment CDATA #REQUIRED>
<!ATTLIST mole_config end CDATA #REQUIRED>
<!ATTLIST mole_config mode CDATA #REQUIRED>
<!ATTLIST mole_config needle CDATA #REQUIRED>
<!ATTLIST mole_config parenthesis CDATA #REQUIRED>
<!ATTLIST mole_config prefix CDATA #REQUIRED>
<!ATTLIST mole_config separator CDATA #REQUIRED>
<!ATTLIST mole_config query_columns CDATA #REQUIRED>
<!ELEMENT dbms_mole (finger)>
<!ATTLIST dbms_mole type CDATA #REQUIRED>
<!ELEMENT finger EMPTY>
<!ATTLIST finger query CDATA #REQUIRED>
<!ATTLIST finger to_search CDATA #REQUIRED>
<!ATTLIST finger is_string_query CDATA #REQUIRED>
<!ELEMENT data_dumper EMPTY>
<!ATTLIST data_dumper type CDATA #REQUIRED>
<!ELEMENT connection EMPTY>
<!ATTLIST connection delay CDATA #REQUIRED>
<!ATTLIST connection method CDATA #REQUIRED>
<!ATTLIST connection headers CDATA #REQUIRED>
<!ATTLIST connection url CDATA #REQUIRED>
<!ATTLIST connection post_parameters CDATA #REQUIRED>
<!ATTLIST connection vulnerable_param CDATA #REQUIRED>
<!ATTLIST connection vulnerable_param_method CDATA #REQUIRED>
<!ELEMENT data_schema (schema*)>
<!ELEMENT schema (table*)>
<!ATTLIST schema name CDATA #REQUIRED>
<!ELEMENT table (column*)>
<!ATTLIST table name CDATA #REQUIRED>
<!ELEMENT column EMPTY>
<!ATTLIST column name CDATA #REQUIRED>
]>
"""

class XMLExporter:

    def export(self, mole, schemata, file_name):
        root = etree.Element('themole')

        #Create Mole Config
        config = etree.Element('config')

        #Create mole_config and append it
        mole_config = self.__export_mole_config(mole)
        config.append(mole_config)
        del mole_config

        dbms_mole = self.__export_dbms_mole(mole)
        config.append(dbms_mole)
        del dbms_mole

        data_dumper = self.__export_data_dumper(mole)
        config.append(data_dumper)
        del data_dumper

        connection = self.__export_connection(mole)
        config.append(connection)
        del connection

        root.append(config)
        del config

        #Create schema tree
        data_schema = etree.Element('data_schema')

        for db_name in schemata:
            schema_entry = self.__export_schema(db_name, schemata[db_name])
            data_schema.append(schema_entry)

        #Append the schema tree to the root.
        root.append(data_schema)

        xml_doc = etree.ElementTree(root)
        try:
            f = open(file_name, "wb")
            xml_doc.write(f, pretty_print=True)
            f.close()
        except IOError:
            raise FileOpenException()

    def load(self, mole_config, schemata, file_name):
        try:
            f = open(file_name, "r")
            xml_string = '<?xml version="1.0" ?>' + dtd + f.read().replace('<?xml version="1.0" ?>', '')
            f.close()
        except IOError:
            raise FileOpenException()

        mole_config.analyser = DomAnalyser()

        try:
            parser = etree.XMLParser(dtd_validation = True)
            root = etree.fromstring(xml_string, parser)
        except etree.XMLSyntaxError:
            raise InvalidFormatException()

        config = root[0]
        try:
            self.__import_mole_config(config[0], mole_config)
            self.__import_dbms_mole(config[1], mole_config)
            self.__import_data_dumper(config[2], mole_config)
            self.__import_connection(config[3], mole_config)

            schemata.clear()
            data_schema = root[1]
            self.__import_schemas(data_schema, schemata)
        except binascii.Error:
            raise InvalidDataException()


    def __export_mole_config(self, mole):
        mole_config = etree.Element('mole_config')

        needle = b64encode(mole.needle.encode()).decode()
        mole_config.set('needle', needle)
        del needle

        mode = b64encode(mole.mode.encode()).decode()
        mole_config.set('mode', mode)
        del mode

        prefix = b64encode(mole.prefix.encode()).decode()
        mole_config.set('prefix', prefix)
        del prefix

        end = b64encode(mole.end.encode()).decode()
        mole_config.set('end', end)
        del end

        separator = b64encode(mole.separator.encode()).decode()
        mole_config.set("separator", separator)
        del separator

        comment = b64encode(mole.comment.encode()).decode()
        mole_config.set("comment", comment)
        del comment

        parenthesis = b64encode(str(mole.parenthesis).encode()).decode()
        mole_config.set("parenthesis", parenthesis)
        del parenthesis

        query_columns = b64encode(str(mole.query_columns).encode()).decode()
        mole_config.set("query_columns", query_columns)
        del query_columns

        return mole_config

    def __import_mole_config(self, node, mole_config):

        value = node.get('needle')
        needle = b64decode(value.encode()).decode()
        mole_config.needle = needle
        del needle

        value = node.get('mode')
        mode = b64decode(value.encode()).decode()
        mole_config.mode = mode
        del mode

        value = node.get('prefix')
        prefix = b64decode(value.encode()).decode()
        mole_config.prefix = prefix
        del prefix

        value = node.get('end')
        end = b64decode(value.encode()).decode()
        mole_config.end = end
        del end

        value = node.get('separator')
        separator = b64decode(value.encode()).decode()
        mole_config.separator = separator
        del separator

        value = node.get('comment')
        comment = b64decode(value.encode()).decode()
        mole_config.comment = comment
        del comment

        value = node.get('parenthesis')
        parenthesis = int(b64decode(value.encode()).decode())
        mole_config.parenthesis = parenthesis
        del parenthesis

        value = node.get('query_columns')
        query_columns = int(b64decode(value.encode()).decode())
        mole_config.query_columns = query_columns
        del query_columns

        return mole_config

    def __export_dbms_mole(self, mole_config):
        dbms_mole_obj = mole_config._dbms_mole

        dbms_mole = etree.Element('dbms_mole')
        dbms_mole_type = b64encode(dbms_mole_obj.dbms_name().encode()).decode()
        dbms_mole.set('type', dbms_mole_type)
        del dbms_mole_type

        finger_obj = mole_config._dbms_mole.finger

        #Create finger node and append it to dbms_mole
        finger = etree.Element("finger")

        dumped_query = dumps(finger_obj._query)
        query = b64encode(dumped_query).decode()
        finger.set("query", query)
        del query

        dumped_query = dumps(finger_obj._to_search)
        to_search = b64encode(dumped_query).decode()
        finger.set("to_search", to_search)
        del to_search

        is_string_query = b64encode(b'1' if finger_obj.is_string_query else b'0').decode()
        finger.set("is_string_query", is_string_query)
        del is_string_query

        dbms_mole.append(finger)

        return dbms_mole

    def __import_dbms_mole(self, node, mole_config):

        dbms_mole_type = b64decode(node.get('type').encode()).decode()
        dbms_mole_class = [c for c in mole_config.dbms_mole_list if c.dbms_name() == dbms_mole_type]
        if len(dbms_mole_class) == 0:
            raise InvalidDataException('Could not find the dbms_mole indicated in the XML file.')
        if len(dbms_mole_class) > 1:
            raise InvalidDataException('Too many dbms_moles match the type string. This should never happen')
        dbms_mole_obj = dbms_mole_class[0]()

        finger = node[0]

        value = finger.get('query')
        query = loads(b64decode(value.encode()))

        value = finger.get('to_search')
        to_search = loads(b64decode(value.encode()))

        value = finger.get('is_string_query')
        is_string_query = b64decode(value.encode()) == b'1'

        finger_obj = FingerBase(query, to_search, is_string_query)

        dbms_mole_obj.finger = finger_obj

        mole_config._dbms_mole = dbms_mole_obj

    def __export_data_dumper(self, mole_config):

        data_dumper = etree.Element('data_dumper')

        type_ = b64encode(mole_config.dumper.name.encode()).decode()
        data_dumper.set("type", type_)

        return data_dumper

    def __import_data_dumper(self, node, mole_config):

        type_ = node.get('type')
        value = b64decode(type_.encode()).decode()

        data_dumper_class = datadumper_classes.get(value, None)

        if data_dumper_class is None:
            InvalidDataException('Could not find the data_dumper indicated in the XML file.')

        data_dumper_obj = data_dumper_class()
        mole_config.dumper = data_dumper_obj

    def __export_connection(self, mole_config):

        conn_obj = mole_config.requester
        connection = etree.Element('connection')

        delay = b64encode(str(conn_obj.delay).encode()).decode()
        connection.set('delay', delay)
        del delay

        method = b64encode(conn_obj.method.encode()).decode()
        connection.set('method', method)
        del method

        headers = b64encode(dumps(conn_obj.headers)).decode()
        connection.set('headers', headers)
        del headers

        url = b64encode(conn_obj.get_url().encode()).decode()
        connection.set('url', url)
        del url

        post_params = b64encode(conn_obj.get_post_params().encode()).decode()
        connection.set('post_parameters', post_params)
        del post_params

        vulnerable_param = b64encode(conn_obj.vulnerable_param.encode()).decode()
        connection.set('vulnerable_param', vulnerable_param)
        del vulnerable_param

        vulnerable_param_method = b64encode(conn_obj.vulnerable_param_group.encode()).decode()
        connection.set('vulnerable_param_method', vulnerable_param_method)
        del vulnerable_param_method

        return connection

    def __import_connection(self, node, mole_config):

        conn_obj = mole_config.requester

        field = node.get('delay')
        value = int(b64decode(field.encode()).decode())
        conn_obj.delay = value

        field = node.get('method')
        value = b64decode(field.encode()).decode()
        conn_obj.method = value

        field = node.get('headers')
        value = loads(b64decode(field.encode()))
        conn_obj.headers = value

        field = node.get('url')
        value = b64decode(field.encode()).decode()
        conn_obj.set_url(value)

        field = node.get('post_parameters')
        value = b64decode(field.encode()).decode()
        conn_obj.set_post_params(value)

        field = node.get('vulnerable_param')
        value = b64decode(field.encode()).decode()
        conn_obj.vulnerable_param = value

        field = node.get('vulnerable_param_method')
        value = b64decode(field.encode()).decode()
        conn_obj.vulnerable_param_group = value

    def __export_schema(self, name, db):
        #Create the schema entry
        schema_entry = etree.Element('schema')
        schema_entry.set('name', b64encode(name.encode()).decode())

        for table_name in db:
            #Create the table entry
            table_entry = self.__export_table(table_name, db[table_name])
            schema_entry.append(table_entry)

        return schema_entry

    def __export_table(self, name, table):

        table_entry = etree.Element('table')
        table_entry.set('name', b64encode(name.encode()).decode())
        for column in table:
            #Create the column entry and store it in the table
            column_entry = etree.Element("column")
            column_entry.set('name', b64encode(column.encode()).decode())
            table_entry.append(column_entry)
        return table_entry

    def __import_schemas(self, data_schema, schemata):

        for schema in data_schema:
            table_dict = {}
            for table in schema:
                column_list = [b64decode(col.get('name').encode()).decode() for col in table]
                table_dict[b64decode(table.get('name').encode()).decode()] = column_list
            schemata[b64decode(schema.get('name').encode()).decode()] = table_dict
