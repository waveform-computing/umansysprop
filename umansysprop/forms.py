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
import decimal

import pybel
from flask import request
from flask.ext.wtf import Form as BaseForm
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

from .html import html, literal, content, tag


Form = BaseForm


class SubForm(BaseForm):
    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(SubForm, self).__init__(*args, csrf_enabled=False, **kwargs)


def smiles(s):
    """
    Converts *s* into an OpenBabel :class:`Molecule` object. Raises
    :exc:`ValueError` if *s* is not a valid SMILES string.
    """
    if isinstance(s, str):
        s = s.encode('ascii')
    try:
        return pybel.readstring(b'smi', s)
    except IOError:
        raise ValueError('"%s" is not a valid SMILES string' % s)


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
            kwargs['list'] = '%s-list' % self.id
        return super(SMILESField, self).__call__(**kwargs)

    @property
    def scripts(self):
        return tag.datalist(
            (
                tag.option(value, label=label)
                for (value, label) in self.compounds
                ),
            id='%s-list' % self.id
            )

    def _value(self):
        if self.data:
            return self.data.write(b'smi').decode('ascii')
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = smiles(valuelist[0])
        else:
            self.data = None


class SMILESDictField(FormField):
    """
    Represents a compound input which defines a mapping of SMILES strings to
    floating point values, or accepts a file upload containing one SMILES
    string and one floating point value separated by whitespace, per line. The
    field's data is returned as a mapping of OpenBabel Molecule objects to
    float values.

    Additional keyword arguments introduced by this class are:

    :param entry_label:
        Provides the label appearing above the SMILES text entry field

    :param data_label:
        Provides the label appearing above the floating point entry field

    :param upload_label:
        Provides the label appearing beside the file upload field

    :param compounds:
        If provided, a sequence of ``(value, label)`` tuples which can be
        selected by drop-down from the text-entry field. Defaults to an empty
        sequence.

    :param min_entries:
        The minimum number of entries permitted in the field. Defaults to 0.

    :param max_entries:
        The maximum number of entries permitted in the field. Defaults to 100.
    """

    def __init__(self, label=None, entry_label=None, data_label=None,
            upload_label=None, validators=None, compounds=None, separator='-',
            min_entries=0, max_entries=100, **kwargs):

        class MapForm(SubForm):
            smiles = SMILESField(entry_label, compounds=compounds)
            data = FloatField(data_label)

        class ListForm(SubForm):
            entry = FieldList(
                FormField(MapForm),
                min_entries=min_entries, max_entries=max_entries)
            upload = FileField(upload_label)

        super(SMILESDictField, self).__init__(
                ListForm, label, separator=separator, **kwargs)

    @property
    def data(self):
        if self.form.upload.name in request.files:
            try:
                result = {
                    smiles(key): float(value)
                    for i, _line in enumerate(
                        request.files[self.form.upload.name].read().splitlines(),
                        start=1)
                    for line in (_line.strip(),)
                    for key, value in (line.split(None, 1),)
                    if line and not line.startswith('#')
                    }
            except ValueError as e:
                e.args += ('on line %d' % i)
                raise
        else:
            result = {
                e.smiles.data: e.data.data
                for e in self.form.entry
                }
        min_len = self.form.entry.min_entries
        max_len = self.form.entry.max_entries
        if len(result) < min_len:
            raise ValueError(
                'not enough entries (%d); expected at least %d' %
                (len(result), min_len))
        if len(result) > max_len:
            raise ValueError(
                'too many entries (%d); maximum %d' %
                (len(result), max_len))
        return result

    def __call__(self, **kwargs):
        if not len(self.form.entry):
            self.form.entry.append_entry()
        # XXX Layout specific to UManSysProp
        return tag.div(
            tag.div(
                tag.div(
                    tag.label(
                        tag.input(
                            type='checkbox',
                            value='file'
                            ),
                        ' upload file',
                        ),
                    class_='small-12 columns'
                    ),
                class_='row'
                ),
            tag.div(
                tag.div(
                    self.form.upload,
                    class_='small-12 columns'
                    ),
                class_='row',
                data_toggle='fieldset-upload'
                ),
            tag.div(
                tag.div(
                    self.form.entry[0].smiles.label(class_='inline'),
                    class_='small-6 columns'
                    ),
                tag.div(
                    self.form.entry[0].data.label(class_='inline'),
                    class_='medium-4 small-3 columns'
                    ),
                tag.div(
                    tag.a('Add', class_='button tiny right', data_toggle='fieldset-add-row'),
                    class_='medium-2 small-3 columns clearfix'
                    ),
                class_='row',
                data_toggle='fieldset-entry'
                ),
            (tag.div(
                tag.div(
                    entry.smiles,
                    class_='small-6 columns'
                    ),
                tag.div(
                    entry.data,
                    class_='medium-4 small-3 columns'
                    ),
                tag.div(
                    tag.a('Remove', class_='button tiny right', data_toggle='fieldset-remove-row'),
                    class_='medium-2 small-3 columns clearfix'
                    ),
                class_='row',
                data_toggle='fieldset-entry'
                ) for entry in self.form.entry),
            id=self.id,
            data_toggle='fieldset',
            data_freeid=len(self.form.entry)
            )

    @property
    def scripts(self):
        template = """\
$('div#%(id)s').each(function() {
    var $field = $(this);
    var $check = $field.find(':checkbox');
    var $add = $field.find('a[data-toggle=fieldset-add-row]');
    var $remove = $field.find('a[data-toggle=fieldset-remove-row]');
    var $upload = $field.find('div[data-toggle=fieldset-upload]');
    var freeid = parseInt($field.data('freeid'));

    $add.click(function() {
        // Find the last row and clone it
        var $oldrow = $field.find('div[data-toggle=fieldset-entry]:last');
        var $row = $oldrow.clone(true);
        // Re-write the ids of the input in the row
        $row.find(':input').each(function() {
            var newid = $(this).attr('id').replace(
                /%(id)s-entry-(\d{1,4})/,
                '%(id)s-entry-' + freeid);
            $(this)
                .attr('name', newid)
                .attr('id', newid)
                .val('')
                .removeAttr('checked');
        });
        $oldrow.after($row);
        freeid++;
    });

    $remove.click(function() {
        if ($field.find('div[data-toggle=fieldset-entry]').length > 2) {
            var thisRow = $(this).closest('div[data-toggle=fieldset-entry]');
            thisRow.remove();
        }
    });

    $check.change(function() {
        // Refresh the entry matches
        var $entry = $field.find('div[data-toggle=fieldset-entry]');

        var $show = this.checked ? $upload : $entry;
        var $hide = this.checked ? $entry : $upload;
        $hide.fadeOut('fast', function() {
            $hide
                .find(':input')
                    .prop('disabled', true);
            $show
                .find(':input')
                    .prop('disabled', false)
                .end()
                    .fadeIn('fast');
        });
    });

    if ($field.find(':file').val()) {
        $check.prop('checked', true);
        $field.find('div[data-toggle=fieldset-entry]')
            .hide().find(':input').prop('disabled', true);
    }
    else {
        $check.prop('checked', false);
        $upload
            .hide().find(':input').prop('disabled', true);
    }
});
"""
        return literal('\n'.join(
            [tag.script(literal(template % {'id': self.id}))] +
            [entry.smiles.scripts for entry in self.form.entry]
            ))


class SMILESListField(FormField):
    """
    Represents a compound input which defines a list of SMILES strings
    representing chemical compounds, or accepts a file upload containing one
    SMILES string per line. The field's data is returned as a sequence of
    OpenBabel Molecule objects.

    Additional keyword arguments introduced by this class are:

    :param entry_label:
        Provides the label appearing above the SMILES text entry field

    :param upload_label:
        Provides the label appearing beside the file upload field

    :param compounds:
        If provided, a sequence of ``(value, label)`` tuples which can be
        selected by drop-down from the text-entry field. Defaults to an empty
        sequence.

    :param min_entries:
        The minimum number of entries permitted in the field. Defaults to 0.

    :param max_entries:
        The maximum number of entries permitted in the field. Defaults to 100.
    """

    def __init__(self, label=None, entry_label=None, upload_label=None,
            validators=None, compounds=None, separator='-', min_entries=0,
            max_entries=100, **kwargs):

        class ListForm(SubForm):
            entry = FieldList(
                SMILESField(entry_label, validators=validators, compounds=compounds),
                min_entries=min_entries, max_entries=max_entries)
            upload = FileField(upload_label)

        super(SMILESListField, self).__init__(
                ListForm, label, separator=separator, **kwargs)

    @property
    def data(self):
        if self.form.upload.name in request.files:
            try:
                result = [
                    smiles(line)
                    for i, _line in enumerate(
                        request.files[self.form.upload.name].read().splitlines(),
                        start=1
                        )
                    for line in (_line.strip(),)
                    if line and not line.startswith('#')
                    ]
            except ValueError as e:
                raise ValueError('%s on line %d' % (str(e), i))
        else:
            result = self.form.entry.data
        min_len = self.form.entry.min_entries
        max_len = self.form.entry.max_entries
        if len(result) < min_len:
            raise ValueError(
                'not enough entries (%d); expected at least %d' %
                (len(result), min_len))
        if len(result) > max_len:
            raise ValueError(
                'too many entries (%d); maximum %d' %
                (len(result), max_len))
        return result

    def __call__(self, **kwargs):
        if not len(self.form.entry):
            self.form.entry.append_entry()
        # XXX Layout specific to UManSysProp
        return tag.div(
            tag.div(
                tag.div(
                    tag.label(
                        tag.input(
                            type='checkbox',
                            value='file'
                            ),
                        ' upload file',
                        ),
                    class_='medium-10 small-9 columns'
                    ),
                tag.div(
                    tag.a('Add', class_='button tiny right', data_toggle='fieldset-add-row'),
                    class_='medium-2 small-3 columns clearfix'
                    ),
                class_='row'
                ),
            tag.div(
                tag.div(
                    self.form.upload,
                    class_='small-12 columns'
                    ),
                class_='row',
                data_toggle='fieldset-upload'
                ),
            (tag.div(
                tag.div(
                    field,
                    class_='medium-10 small-9 columns'
                    ),
                tag.div(
                    tag.a('Remove', class_='button tiny right', data_toggle='fieldset-remove-row'),
                    class_='medium-2 small-3 columns clearfix'
                    ),
                class_='row',
                data_toggle='fieldset-entry'
                ) for field in self.form.entry),
            id=self.id,
            data_toggle='fieldset',
            data_freeid=len(self.form.entry)
            )

    @property
    def scripts(self):
        template = """\
$('div#%(id)s').each(function() {
    var $field = $(this);
    var $check = $field.find(':checkbox');
    var $add = $field.find('a[data-toggle=fieldset-add-row]');
    var $remove = $field.find('a[data-toggle=fieldset-remove-row]');
    var $upload = $field.find('div[data-toggle=fieldset-upload]');
    var freeid = parseInt($field.data('freeid'));

    $add.click(function() {
        // Find the last row and clone it
        var $oldrow = $field.find('div[data-toggle=fieldset-entry]:last');
        var $row = $oldrow.clone(true);
        // Re-write the ids of the input in the row
        $row.find(':input').each(function() {
            var newid = $(this).attr('id').replace(
                /%(id)s-entry-(\d{1,4})/,
                '%(id)s-entry-' + freeid);
            $(this)
                .attr('name', newid)
                .attr('id', newid)
                .val('')
                .removeAttr('checked');
        });
        $oldrow.after($row);
        freeid++;
    });

    $remove.click(function() {
        if ($field.find('div[data-toggle=fieldset-entry]').length > 1) {
            var thisRow = $(this).closest('div[data-toggle=fieldset-entry]');
            thisRow.remove();
        }
    });

    $check.change(function() {
        // Refresh the entry matches
        var $entry = $field.find('div[data-toggle=fieldset-entry]').add($add);

        var $show = this.checked ? $upload : $entry;
        var $hide = this.checked ? $entry : $upload;
        $hide.fadeOut('fast', function() {
            $hide
                .find(':input')
                    .prop('disabled', true);
            $show
                .find(':input')
                    .prop('disabled', false)
                .end()
                    .fadeIn('fast');
        });
    });

    if ($field.find(':file').val()) {
        $check.prop('checked', true);
        $field.find('div[data-toggle=fieldset-entry]').add($add)
            .hide().find(':input').prop('disabled', true);
    }
    else {
        $check.prop('checked', false);
        $upload
            .hide().find(':input').prop('disabled', true);
    }
});
"""
        return literal('\n'.join(
            [tag.script(literal(template % {'id': self.id}))] +
            [field.scripts for field in self.form.entry]
            ))


class FloatRangeField(FormField):
    """
    Represents a complex input which defines either a single floating point
    value, or a range of floating point values evenly spaced between two
    inclusive end-points. In either case, the field returns a sequence of
    floating point values as its data.

    :param max_entries:
        Defines the maximum number of values in the sequence. Defaults to 1000.
    """

    def __init__(
            self, label=None, validators=None, separator='-', max_entries=1000,
            **kwargs):
        validators = validators or []
        self._min = None
        self._max = None
        for v in validators:
            if isinstance(v, NumberRange):
                self._min = v.min
                self._max = v.max
                break

        class RangeForm(SubForm):
            count = IntegerField(
                'values', default=1,
                validators=
                    [v for v in validators if isinstance(v, InputRequired)] +
                    [NumberRange(min=1, max=max_entries)]
                )
            start = FloatField(
                'values from', default=kwargs.get('default'),
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
                tag.div(
                    tag.label(
                        tag.input(
                            type='checkbox',
                            value='range'
                            ),
                        ' range'
                        ),
                    class_='small-12 columns'
                    ),
                class_='row'
                ),
            tag.div(
                tag.div(
                    self.form.start(id=self.form.start.id + '-single', min=self._min, max=self._max),
                    self.form.stop(id=self.form.stop.id + '-single', type='hidden'),
                    self.form.count(id=self.form.count.id + '-single', type='hidden', value=1),
                    class_='small-12 columns'
                    ),
                class_='row',
                data_toggle='single'
                ),
            tag.div(
                tag.div(
                    self.form.count(min=1),
                    class_='medium-3 columns',
                    data_toggle='count'
                    ),
                tag.div(
                    self.form.start.label(class_='inline'),
                    class_='medium-2 columns medium-text-center'
                    ),
                tag.div(
                    self.form.start(min=self._min, max=self._max),
                    class_='medium-3 columns'
                    ),
                tag.div(
                    self.form.stop.label(class_='inline'),
                    class_='medium-1 columns medium-text-center'
                    ),
                tag.div(
                    self.form.stop(min=self._min, max=self._max),
                    class_='medium-3 columns'
                    ),
                class_='row',
                data_toggle='multi'
                ),
            id=self.id
            )

    @property
    def scripts(self):
        template = """\
$('div#%(id)s').each(function() {
    var $field = $(this);
    var $check = $field.find(':checkbox');
    var $single = $field.find('div[data-toggle=single]');
    var $multi = $field.find('div[data-toggle=multi]');

    $single.find('#%(id)s-start-single').change(function() {
        $single.find('#%(id)s-stop-single').val($(this).val());
    });

    $check.change(function() {
        $show = this.checked ? $multi : $single;
        $hide = this.checked ? $single : $multi;
        $hide.fadeOut('fast', function() {
            $hide
                .find(':input')
                    .prop('disabled', true);
            $show
                .find(':input')
                    .prop('disabled', false)
                .end()
                    .fadeIn('fast');
        });
    });

    if (parseInt($multi.find('#%(id)s-count').val()) > 1) {
        $check.prop('checked', true);
        $single.hide().find(':input').prop('disabled', true);
        $multi.find(':input').prop('disabled', false);
    }
    else {
        $check.prop('checked', false);
        $multi.hide().find(':input').prop('disabled', true);
        $single.find(':input').prop('disabled', false);
    }

});
"""
        return tag.script(literal(template % {'id': self.id}))

    @property
    def data(self):
        start = self.form.start.data
        stop = self.form.stop.data
        count = self.form.count.data
        if count == 1:
            return [start]
        else:
            step = (stop - start) / (count - 1)
            return list(frange(start, stop, step)) + [stop]


def convert_args(form, args):
    """
    Given a *form* and a dictionary of *args* which has been decoded from JSON,
    returns *args* with the type of each value converted for the corresponding
    field.
    """
    conversion = {
        IntegerField:    int,
        FloatField:      float,
        DecimalField:    decimal.Decimal,
        BooleanField:    bool,
        SMILESField:     smiles,
        SMILESListField: lambda l: [smiles(s) for s in l],
        SMILESDictField: lambda l: {smiles(s): float(v) for (s, v) in l.items()},
        FloatRangeField: lambda l: [float(f) for f in l],
        }
    return {
        field.name: conversion.get(field.__class__, lambda x: x)(args[field.name])
        for field in form
        if field.name != 'csrf_token'
        }

