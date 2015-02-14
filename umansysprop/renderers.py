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


import sys
import io
import csv
import tempfile

import xlsxwriter as xl
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


@register('application/json', 'JSON file')
def render_json(obj, **kwargs):
    return json.dumps(obj, **kwargs)


@register('application/csv', 'CSV file', {
        'Content-Disposition': 'attachment; filename=umansysprop.zip',
        })
def render_csv(obj, **kwargs):

    def process_table(table_id):
        col_keys = sorted(obj[table_id].keys())
        row_keys = sorted(obj[table_id][col_keys[0]].keys())
        # Deal with incompatibility between Py2 and Py3's CSV writer
        if sys.version_info.major == 3:
            stream = io.StringIO(newline='')
        else:
            stream = io.BytesIO()
        writer = csv.writer(stream)
        writer.writerow([obj['tables'][table_id]['rows'][2]] + col_keys)
        for row_key in row_keys:
            writer.writerow([row_key] + [obj[table_id][col_key][row_key] for col_key in col_keys])
        stream.seek(0)
        return stream

    with io.BytesIO() as stream:
        with ZipFile(stream, 'w', compression=ZIP_DEFLATED) as archive:
            archive.comment = '\n'.join(
                obj['tables'][table_id]['title']
                for table_id in obj['tables']
                ).encode('utf-8')
            for table_id in obj['tables']:
                archive.write(process_table(table_id), obj['tables'][table_id]['title'] + '.csv')
        return stream.getvalue()


@register('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel file', {
        'Content-Disposition': 'attachment; filename=umansysprop.xlsx',
        })
def render_xlsx(obj, **kwargs):
    stream = io.BytesIO()
    workbook = xl.Workbook(stream, {'in_memory': True})
    bold = workbook.add_format({'bold': True})

    def process_table(table_id, worksheet):
        col_keys = sorted(obj[table_id].keys())
        row_keys = sorted(obj[table_id][col_keys[0]].keys())
        worksheet.title = obj['tables'][table_id]['title']
        worksheet.merge_range(0, 1, 0, len(col_keys), obj['tables'][table_id]['cols'][2], bold)
        worksheet.write(1, 0, obj['tables'][table_id]['rows'][2], bold)
        for col, col_key in enumerate(col_keys, start=1):
            worksheet.write(1, col, col_key)
        for row, row_key in enumerate(row_keys, start=2):
            worksheet.write(row, 0, row_key)
            for col, col_key in enumerate(col_keys, start=1):
                worksheet.write(row, col, obj[table_id][col_key][row_key])

    for table_id in obj['tables']:
        process_table(table_id, workbook.add_worksheet(obj['tables'][table_id]['title']))
    workbook.close()
    return stream.getvalue()


@register('application/xml', 'XML file', {
        'Content-Disposition': 'attachment; filename=umansysprop.xml',
        })
def render_xml(obj, **kwargs):
    tag = TagFactory(xml=True)

    def process_table(table_id):
        col_keys = sorted(obj[table_id].keys())
        row_keys = sorted(obj[table_id][col_keys[0]].keys())
        return tag.table(
            tag.columns(
                (tag.column(id=col_key) for col_key in col_keys),
                title=obj['tables'][table_id]['cols'][2]
                ),
            tag.rows((
                tag.row(
                    (tag.data(value=obj[table_id][col_key][row_key]) for col_key in col_keys),
                    id=row_key
                ) for row_key in row_keys),
                title=obj['tables'][table_id]['rows'][2]
                ),
            id=table_id,
            title=obj['tables'][table_id]['title']
            )

    return tag.tables(process_table(table_id) for table_id in obj['tables'])


@register('text/html', 'HTML (view in web browser)')
def render_html(obj, **kwargs):
    tag = TagFactory(xml=False)

    def render_table(table_id):
        col_keys = sorted(obj[table_id].keys())
        row_keys = sorted(obj[table_id][col_keys[0]].keys())
        return tag.table(
            tag.caption(obj['tables'][table_id]['title']),
            tag.thead(
                tag.tr(
                    tag.th(''),
                    tag.th(obj['tables'][table_id]['cols'][2], colspan=len(col_keys)),
                    ),
                tag.tr(
                    tag.th(obj['tables'][table_id]['rows'][2]),
                    *(tag.th(key) for key in col_keys)
                    )
                ),
            tag.tbody((
                tag.tr(
                    tag.th(row_key),
                    *(tag.td(obj[table_id][col_key][row_key]) for col_key in col_keys)
                    )
                for row_key in row_keys),
                ),
            )

    return tag.div(render_table(table_id) for table_id in obj['tables'])

