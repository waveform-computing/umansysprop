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


from flask import json

from .html import TagFactory


def render_json(obj, **kwargs):
    return json.dumps(obj, **kwargs)


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

