# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright 2014 Dave Hughes <dave@waveform.org.uk>.
#
# This file is part of umansysprop.
#
# umansysprop is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 2 of the License, or (at your option) any later
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
Demo function
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')


from ..forms import *
from ..results import Result, Table


class HandlerForm(Form):
    temperatures = FloatRangeField(
        'Temperature', validators=[
            Length(min=1, max=100, message='Temperatures must have between 1 and 100 values'),
            NumberRange(min=0.0, max=100.0, message='Temperatures must be between 0 and 100 celsius'),
            ])
    scale1 = IntegerField('Scaling factor 1')
    scale2 = IntegerField('Scaling factor 2')
    compounds = SMILESListField(
        'Compounds',
        compounds=[
            ('C(CC(=O)O)C(=O)O',                 'Succinic acid'),
            ('C(=O)(C(=O)O)O',                   'Oxalic acid'),
            ('O=C(O)CC(O)=O',                    'Malonic acid'),
            ('CCCCC/C=C/C/C=C/CC/C=C/CCCC(=O)O', 'Pinolenic acid'),
            ])


def handler(temperatures, scale1, scale2, compounds):
    return Result(
        Table(
            'temps',
            title='Demo 1',
            rows=temperatures, rows_title='Temperatures',
            cols=[scale1, scale2], cols_title='Scaling factors',
            func=lambda t, s: t * s,
            ),
        Table(
            'formulae',
            title='Demo 2',
            rows=compounds, rows_title='Compounds',
            cols=['Formula'], cols_title='Result',
            func=lambda c, _: c.formula,
            )
        )

