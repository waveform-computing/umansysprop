# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright 2014 Dave Hughes <dave@waveform.org.uk>.
#
# This file is part of umansysprop.
#
# umansysprop is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# umansysprop is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# umansysprop.  If not, see <http://www.gnu.org/licenses/>.

"""
A module demonstrating the construction of calculations for the UManSysProp web
server.
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')


from wtforms import Form as BaseForm
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired


class Form(BaseForm):
    number1 = IntegerField('First number', validators=[InputRequired()])
    number2 = IntegerField('Second number', validators=[InputRequired()])


def handler(number1, number2):
    return {'result': number1 + number2}

