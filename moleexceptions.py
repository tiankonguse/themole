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

#General Exceptions

class StoppedQueryException(Exception):
    pass

#The Mole Exceptions

class PageNotFound(Exception):
    pass

class SQLInjectionNotDetected(Exception):
    pass

class SQLInjectionNotExploitable(Exception):
    pass

class MoleAttributeRequired(Exception):
    pass

class DbmsDetectionFailed(Exception):
    pass

class NotInitializedException(Exception):
    pass

class EncodingNotFound(Exception):
    pass

#Command Exceptions

class CmdNotFoundException(Exception):
    pass

class CommandException(Exception):
    def __init__(self, message, print_usage=True):
        Exception.__init__(self, message)
        self.print_usage = print_usage

class QuietCommandException(Exception):
    pass


#Domanalyser Exception

class NeedleNotFound(Exception):
    pass

#InjectionInspector Exceptions

class ColumnNumberNotFound(Exception):
    pass

class SeparatorNotFound(Exception):
    pass

class CommentNotFound(Exception):
    pass

class InjectableFieldNotFound(Exception):
    pass

class InvalidParamException(Exception):
    pass

class InvalidMethodException(Exception):
    pass

#Filter exceptions

class FilterRuntimeException(Exception):
    pass

class FilterNotFoundException(Exception):
    pass

class FilterConfigException(Exception):
    pass

#DataDumper Exceptions

class QueryError(Exception):
    pass

#Connection Exceptions

class ConnectionException(Exception):
    pass

# XML Exporter

class FileOpenException(Exception):
    pass

class InvalidFormatException(Exception):
    pass

class InvalidDataException(Exception):
    pass

# HTMLFilter

class FilterCreationError(Exception):
    pass
