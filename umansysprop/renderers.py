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

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')
try:
    from itertools import izip as zip
except ImportError:
    pass


import sys
import io
import csv
import pickle
import tempfile

import xlsxwriter as xl
import pybel
from flask import json

from .zip import ZipFile, ZIP_DEFLATED
from .html import TagFactory


_RENDERERS = {}

def register(mimetype, label, headers=None):
    if headers is None:
        headers = {}
    def decorator(func):
        if mimetype in _RENDERERS:
            raise ValueError('A handler for MIME-type %s already exists' % mimetype)
        _RENDERERS[mimetype] = (label, headers, func)
        return func
    return decorator

def registered():
    return [
        (mimetype, label)
        for (mimetype, (label, headers, func)) in _RENDERERS.items()
        ]

def render(mimetype, obj, **kwargs):
    try:
        label, headers, func = _RENDERERS[mimetype]
    except KeyError:
        raise ValueError('Unknown MIME-type %s' % mimetype)
    else:
        return headers, func(obj, **kwargs)


def _format_key(value):
    # This rather hacky routine is here to deal with the crappy string
    # conversion from OpenBabel's Molecule class
    if isinstance(value, tuple):
        return tuple(_format_key(key) for key in value)
    elif isinstance(value, pybel.Molecule):
        return str(value).strip()
    else:
        return value


@register('application/json', 'JSON file')
def render_json(results, **kwargs):

    def render_table(table):
        return {
            'name': table.name,
            'title': table.title,
            'rows_title': table.rows_title,
            'cols_title': table.cols_title,
            'data': [
                {
                    'key': (_format_key(row_key), _format_key(col_key)),
                    'value': table.data[(row_key, col_key)],
                    }
                for row_key in table.rows
                for col_key in table.cols
                ]
            }

    return json.dumps([render_table(table) for table in results], **kwargs)


@register('application/octet-stream', 'Python pickle')
def render_pickle(results, **kwargs):
    for table in results:
        # Force evaluation of the data and wipe the function reference (it's
        # no longer needed and typically prevents serialization by being a
        # lambda of some sorts)
        table.data
    return pickle.dumps(results, protocol=0)


@register('application/xml', 'XML file', headers={
        'Content-Disposition': 'attachment; filename=umansysprop.xml',
        })
def render_xml(results, **kwargs):
    tag = TagFactory(xml=True)

    def render_table(table):
        return tag.table(
            tag.columns(
                (tag.column(id=str(col_key)) for col_key in table.cols),
                title=table.cols_title
                ),
            tag.rows((
                tag.row(
                    (tag.data(value=table.data[(row_key, col_key)]) for col_key in table.cols),
                    id=str(row_key)
                ) for row_key in table.rows),
                title=table.rows_title
                ),
            title=table.title,
            name=table.name,
            )

    return tag.tables(render_table(table) for table in results)


@register('application/zip', 'Zipped CSV files', headers={
        'Content-Disposition': 'attachment; filename=umansysprop.zip',
        })
def render_csv(results, **kwargs):

    def render_table(table):
        # Deal with incompatibility between Py2 and Py3's CSV writer
        if sys.version_info.major == 3:
            stream = io.StringIO(newline='')
        else:
            stream = io.BytesIO()
        writer = csv.writer(stream)
        for dim in range(table.col_dims):
            writer.writerow(
                [''] * table.row_dims +
                [_format_key(col_key[dim]) for col_key in table.cols_iter]
                )
        for data_row, row_keys in zip(table.rows, table.rows_iter):
            writer.writerow(
                [_format_key(row_key) for row_key in row_keys] +
                [table.data[(data_row, data_col)] for data_col in table.cols]
                )
        stream.seek(0)
        return stream

    with io.BytesIO() as stream:
        with ZipFile(stream, 'w', compression=ZIP_DEFLATED) as archive:
            archive.comment = '\n'.join(table.title for table in results).encode('utf-8')
            for table in results:
                archive.write(render_table(table), '%s.csv' % table.name)
        return stream.getvalue()


@register('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel file', headers={
        'Content-Disposition': 'attachment; filename=umansysprop.xlsx',
        })
def render_xlsx(results, **kwargs):
    stream = io.BytesIO()
    workbook = xl.Workbook(stream, {'in_memory': True})
    bold = workbook.add_format({'bold': True})

    def render_table(table):
        worksheet = workbook.add_worksheet(table.title[:31])
        # Write column and row titles
        worksheet.merge_range(
            0, table.row_dims, 0, table.row_dims + len(table.cols) - 1,
            table.col_titles[0], bold)
        for col_ix, row_title in enumerate(table.row_titles):
            worksheet.write(
                table.col_dims, col_ix, row_title, bold)
        # Write column keys
        for col_ix, col_key in enumerate(table.cols_iter, start=table.row_dims):
            span = table.col_spans[col_key]
            for col_dim in range(table.col_dims):
                if span[col_dim] > 1:
                    worksheet.merge_range(
                        col_dim + 1, col_ix,
                        col_dim + 1, col_ix + span[col_dim] - 1,
                        _format_key(col_key[col_dim]))
                elif span[col_dim] == 1:
                    worksheet.write(
                        col_dim + 1, col_ix,
                        _format_key(col_key[col_dim]))
        # Write row keys
        for row_ix, row_key in enumerate(table.rows_iter, start=table.col_dims + 1):
            span = table.row_spans[row_key]
            for row_dim in range(table.row_dims):
                if span[row_dim] > 1:
                    worksheet.merge_range(
                        row_ix, row_dim,
                        row_ix + span[row_dim] - 1, row_dim,
                        _format_key(row_key[row_dim]))
                elif span[row_dim] == 1:
                    worksheet.write(
                        row_ix, row_dim,
                        _format_key(row_key[row_dim]))
        # Write data
        for row_ix, row_key in enumerate(table.rows, start=table.col_dims + 1):
            for col_ix, col_key in enumerate(table.cols, start=table.row_dims):
                worksheet.write(row_ix, col_ix, table.data[(row_key, col_key)])

    for table in results:
        render_table(table)
    workbook.close()
    return stream.getvalue()


@register('text/html', 'HTML (view in web browser)')
def render_html(obj, **kwargs):
    tag = TagFactory(xml=False)

    def render_table(table):
        return tag.table(
            tag.caption(obj['tables'][table_id]['title']),
            tag.thead(
                tag.tr(
                    (tag.th('') for i in range(table.row_dims)),
                    tag.th(table.col_titles[0], colspan=len(table.cols)),
                    ),
                (
                    tag.tr(
                        (tag.th('') for i in range(table.row_dims))
                        if col_dim < table.col_dims - 1 else
                        (tag.th(row_title) for row_title in table.row_titles),
                        (
                            tag.th(_format_key(key[col_dim]), colspan=span if span > 1 else None)
                            for key in table.cols_iter
                            for span in (table.col_spans[key][col_dim],)
                            if span > 0
                            )
                        )
                    for col_dim in range(table.col_dims)
                    )
                ),
            tag.tbody(
                tag.tr(
                    (
                        tag.th(_format_key(row_key[row_dim]), rowspan=span if span > 1 else None)
                        for row_dim in range(table.row_dims)
                        for span in (table.row_spans[row_key][row_dim],)
                        if span > 0
                        ),
                    (
                        tag.td(table.data[(data_row, data_col)])
                        for (data_col, col_key) in zip(table.cols, table.cols_iter)
                        )
                    )
                for (data_row, row_key) in zip(table.rows, table.rows_iter)
                ),
            id=table.name,
            )

    return tag.div(render_table(table_id) for table_id in obj['tables'])

