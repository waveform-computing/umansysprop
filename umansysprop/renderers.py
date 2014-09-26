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
    kwargs.pop('dimensions')
    return json.dumps(obj, **kwargs)


def render_xml(obj, **kwargs):
    tag = TagFactory(xml=True)
    dimensions = kwargs['dimensions']

    def process_obj(obj, dim):
        if dim >= len(dimensions):
            return (obj,)
        else:
            tag_name, description = dimensions[dim]
            return (
                getattr(tag, tag_name)(*process_obj(value, dim + 1), value=key)
                for key, value in obj.items()
                )

    return tag.result(process_obj(obj, 0))


def render_html(obj, **kwargs):
    tag = TagFactory(xml=False)
    dimensions = kwargs['dimensions']

    def render_table(obj, dimensions):
        assert len(dimensions) == 2
        col_keys = sorted(obj.keys())
        row_keys = sorted(obj[col_keys[0]].keys())
        return tag.table(
            tag.thead(
                tag.tr(
                    tag.th(''),
                    tag.th(dimensions[0][1], colspan=len(col_keys)),
                    ),
                tag.tr(
                    tag.th(dimensions[1][1]),
                    *(tag.th(key) for key in col_keys)
                    )
                ),
            tag.tbody(
                tag.tr(
                    tag.th(row_key),
                    *(tag.td(obj[col_key][row_key]) for col_key in col_keys)
                    )
                for row_key in row_keys
                )
            )

    def render_section(obj, dimensions):
        if len(dimensions) > 2:
            for key, value in obj.items():
                return tag.div(
                    tag.h2(key),
                    render_section(value, dimensions[1:])
                    )
        else:
            return render_table(obj, dimensions)

    return render_section(obj, dimensions)


