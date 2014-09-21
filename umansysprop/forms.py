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

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')
try:
    range = xrange
except NameError:
    pass


import math

import pybel
from wtforms import Form
from wtforms.fields import (
    Field,
    BooleanField,
    FloatField as _FloatField,
    RadioField,
    SelectField,
    SelectMultipleField,
    StringField,
    PasswordField,
    TextAreaField,
    HiddenField,
    FileField,
    FormField,
    SubmitField,
    FormField,
    FieldList,
    )
from wtforms.fields.html5 import (
    SearchField,
    TelField,
    URLField,
    EmailField,
    DateField,
    DateTimeField,
    IntegerField,
    DecimalField,
    )
from wtforms.validators import (
    Optional,
    DataRequired,
    Email,
    EqualTo,
    IPAddress,
    MacAddress,
    Length,
    InputRequired,
    NumberRange,
    Regexp,
    URL,
    UUID,
    AnyOf,
    NoneOf,
    )
from wtforms.widgets import TextInput
from wtforms.widgets.html5 import NumberInput
from flask import request

from .html import html, literal, content, tag


class FloatField(_FloatField):
    widget = NumberInput(step='any')


class SMILESField(Field):
    """
    Represents a text input which accepts a SMILES strings representing
    a chemical compound. The field's data is returned as an OpenBabel molecule
    object.

    :param compounds:
        If provided, a sequence of ``(value, label)`` tuples which can be
        selected by drop-down from the text field. Defaults to an empty
        sequence.
    """

    widget = TextInput()
    compounds = ()

    def __init__(self, label=None, validators=None, compounds=None, **kwargs):
        super(SMILESField, self).__init__(label, validators, **kwargs)
        if compounds is not None:
            self.compounds = compounds

    def __call__(self, **kwargs):
        if self.compounds:
            return literal(
                tag.datalist(
                    (
                        tag.option(value, label=label)
                        for (value, label) in self.compounds
                        ),
                    id='%s-list' % self.id
                    ) +
                super(SMILESField, self).__call__(list='%s-list' % self.id)
                )
        else:
            return super(SMILESField, self).__call__(**kwargs)

    def _value(self):
        if self.data:
            return self.data.write(b'smi').decode('ascii')
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = pybel.readstring(b'smi', valuelist[0].encode('ascii'))
            except IOError:
                raise ValueError('"%s" is not a valid SMILES string' % valuelist[0])
        else:
            self.data = None


class SMILESListField(FormField):
    """
    Represents a complex input which either accepts a single SMILES string
    representing a chemical compound, or a file input which accepts an uploaded
    file containing one SMILES string per line. In either case, the field
    returns a sequence of OpenBabel molecule objects.

    :param compounds:
        If provided, a sequence of ``(value, label)`` tuples which can be
        selected by drop-down from the text field. Defaults to an empty
        sequence.
    """

    def __init__(
            self, label=None, validators=None, separator='-', compounds=None,
            **kwargs):

        class ListForm(Form):
            single = SMILESField(
                    'Compound', default='', validators=validators,
                    compounds=compounds)
            multi = FileField('Compounds')

        super(SMILESListField, self).__init__(
                ListForm, label, validators=None, separator=separator,
                **kwargs)

    def __call__(self, **kwargs):
        # XXX The following is specific to the UManSysProp layout
        return tag.div(
            tag.div(
                tag.label(
                    tag.input(
                        id='%s-file' % self.name,
                        type='checkbox',
                        value='file'
                        ),
                    ' file'
                    ),
                class_='medium-2 columns'
                ),
            tag.div(
                self.form.single,
                self.form.multi,
                class_='medium-10 columns'
                ),
            class_='row'
            )

    @property
    def scripts(self):
        template = """\
$(document).ready(function() {
    if ($('#%(multi)s').val()) {
        $('#%(name)s-file').prop('checked', true);
        $('#%(single)s').hide();
        $('#%(single)s').prop('disabled', true);
    }
    else {
        $('#%(name)s-file').prop('checked', false);
        $('#%(multi)s').hide();
        $('#%(multi)s').prop('disabled', true);
    }
});
$('#%(name)s-file').change(function() {
    if (this.checked) {
        $('#%(single)s').fadeOut('fast', function() {
            $('#%(single)s').prop('disabled', true);
            $('#%(multi)s').prop('disabled', false);
            $('#%(multi)s').fadeIn('fast');
        });
    }
    else {
        $('#%(multi)s').fadeOut('fast', function() {
            $('#%(multi)s').prop('disabled', true);
            $('#%(single)s').prop('disabled', false);
            $('#%(single)s').fadeIn('fast');
        });
    }
});
"""
        return tag.script(literal(template % {
            'name': self.name,
            'single': self.form.single.id,
            'multi': self.form.multi.id,
            }))

    @property
    def data(self):
        if self.form.multi.name in request.files:
            try:
                return [
                    pybel.readstring(b'smi', s.strip())
                    for (i, s) in enumerate(
                        request.files[self.form.multi.name].read().splitlines())
                    ]
            except IOError:
                raise ValueError('"%s" is not a valid SMILES string on line %d' % (
                    s, i))
        else:
            return [self.form.single.data]


def frange(start, stop=None, step=1.0):
    """
    Floating point variant of :func:`range`. Note that this variant has several
    inefficiencies compared to the built-in range, notably that reversal of
    the resulting generator relies enumeration of the generator.
    """
    if stop is None:
        stop, start = start, 0.0
    count = int(math.ceil((stop - start) / step))
    return (start + n * step for n in range(count))


class FloatRangeField(FormField):
    """
    Represents a complex input which defines either a single floating point
    value, or a range of floating point values evenly spaced between two
    inclusive end-points. In either case, the field returns a sequence of
    floating point values as its data.

    :param max_count:
        Defines the maximum number of values in the sequence. Defaults to 1000.
    """

    def __init__(
            self, label=None, validators=None, separator='-', max_count=1000,
            **kwargs):
        validators = validators or []
        self._min = None
        self._max = None
        for v in validators:
            if isinstance(v, NumberRange):
                self._min = v.min
                self._max = v.max
                break

        class RangeForm(Form):
            count = IntegerField(
                'values', default=1,
                validators=
                    [v for v in validators if isinstance(v, InputRequired)] +
                    [NumberRange(min=1, max=max_count)]
                )
            start = FloatField(
                'from', default=kwargs.get('default'),
                validators=validators)
            stop = FloatField(
                'to', default=kwargs.get('default'),
                validators=
                    [v for v in validators if not isinstance(v, InputRequired)]
                )

            def validate(self):
                if not super(RangeForm, self).validate():
                    return False
                if self.stop.data is not None and self.start.data > self.stop.data:
                    self.start.errors.append(
                        'Starting value must be less than ending value')
                    return False
                return True

        super(FloatRangeField, self).__init__(
                RangeForm, label, validators=None, separator=separator,
                **kwargs)

    def __call__(self, **kwargs):
        # XXX The following is specific to the UManSysProp layout
        return tag.div(
            tag.div(
                tag.label(
                    tag.input(
                        id='%s-range' % self.name,
                        type='checkbox',
                        value='range'
                        ),
                    ' range'
                    ),
                class_='medium-2 columns'
                ),
            tag.div(
                tag.div(
                    self.form.start(id=self.form.start.id + '-single', min=self._min, max=self._max),
                    self.form.stop(id=self.form.stop.id + '-single', type='hidden'),
                    self.form.count(id=self.form.count.id + '-single', type='hidden', value=1),
                    id='%s-single' % self.name
                    ),
                tag.div(
                    self.form.count(min=1),
                    ' ',
                    self.form.count.label,
                    ' ',
                    self.form.start.label,
                    ' ',
                    self.form.start(min=self._min, max=self._max),
                    ' ',
                    self.form.stop.label,
                    ' ',
                    self.form.stop(min=self._min, max=self._max),
                    id='%s-multi' % self.name,
                    class_='form-inline'
                    ),
                class_='medium-10 columns'
                ),
            class_='row'
            )

    @property
    def scripts(self):
        template = """\
$(document).ready(function() {
    if (parseInt($('#%(count)s').val()) > 1) {
        $('#%(name)s-range').prop('checked', true);
        $('#%(name)s-single').hide();
        $('#%(name)s-single input').prop('disabled', true);
    }
    else {
        $('#%(name)s-range').prop('checked', false);
        $('#%(name)s-multi').hide();
        $('#%(name)s-multi input').prop('disabled', true);
    }
});
$('#%(start)s-single').change(function() {
    $('#%(stop)s-single').val($('#%(start)s-single').val());
});
$('#%(name)s-range').change(function() {
    if (this.checked) {
        $('#%(name)s-single').fadeOut('fast', function() {
            $('#%(name)s-single input').prop('disabled', true);
            $('#%(name)s-multi input').prop('disabled', false);
            $('#%(name)s-multi').fadeIn('fast');
        });
    }
    else {
        $('#%(name)s-multi').fadeOut('fast', function() {
            $('#%(name)s-multi input').prop('disabled', true);
            $('#%(name)s-single input').prop('disabled', false);
            $('#%(name)s-single').fadeIn('fast');
        });
    }
});
"""
        return tag.script(literal(template % {
            'name': self.name,
            'start': self.form.start.name,
            'stop': self.form.stop.name,
            'count': self.form.count.name,
            }))

    @property
    def data(self):
        start = self.form.start.data
        stop = self.form.stop.data
        count = self.form.count.data
        if count == 1:
            yield start
        else:
            step = (stop - start) / (count - 1)
            for n in frange(start, stop, step):
                yield n
            yield stop

