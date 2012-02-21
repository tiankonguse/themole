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

class Parameter:
    def __init__(self, exec_function=None, no_args_str='Expected arguments', invalid_args_function=None):
        self.children = {}
        self.generator = None
        self.exec_function = exec_function
        if invalid_args_function is None:
            invalid_args_function = Parameter.default_inv_args
        self.no_args_str = no_args_str
        self.invalid_args_function = invalid_args_function

    def set_param_generator(self, generator):
        self.generator = generator

    def add_parameter(self, name, param):
        self.children[name] = param

    def parameter_list(self, mole, params):
        if self.generator is not None:
            my_params = self.generator(mole, params)
        else:
            my_params = self.children
        if len(params) > 0:
            if params[0] in my_params:
                return my_params[params[0]].parameter_list(mole, params[1:])
            else:
                return []
        else:
            return my_params.keys()
        
    @classmethod
    def default_inv_args(cls, arg):
        print("Invalid argument '{0}'".format(arg))

    def execute(self, mole, params):
        if len(params) > 0:
            if self.generator is not None:
                my_params = self.generator(mole, params)
            else:
                my_params = self.children
            
            if params[0] in my_params:
                return my_params[params[0]].execute(mole, params[1:])
            else:
                if self.generator is None and len(self.children) > 0:
                    self.invalid_args_function(params[0])
                else:
                    return self._exec(mole, params)
        else:
            return self._exec(mole, params)

    def _exec(self, mole, params):
        if self.exec_function is None:
            output_manager.error(self.no_args_str).line_break()
            return False
        else:
            self.exec_function(mole, params)
            return True

