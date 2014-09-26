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
An online framework for calculating the properties of individual organic
molecules and ensemble mixtures
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')

import sys
import io
import os
import pkgutil

from flask import Flask, request, render_template, make_response

from . import tools
from . import renderers

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def index():
    return render_template(
        'index.html',
        title='Welcome',
        tools=[
            finder.find_module(modname).load_module(modname)
            for (finder, modname, ispkg) in pkgutil.iter_modules(
                tools.__path__, prefix=tools.__name__ + '.')
            if not ispkg and modname != 'template'
            ]
        )

@app.route('/tool/<name>', methods=['GET', 'POST'])
def tool(name):
    # Find and load the module containing the specified tool
    mod_name = '%s.%s' % (tools.__name__, name)
    try:
        mod = sys.modules[mod_name]
    except KeyError:
        loader = pkgutil.get_loader(mod_name)
        mod = loader.load_module(mod_name)
    assert hasattr(mod, 'HandlerForm')
    assert hasattr(mod, 'handler')

    # Present the tool's input form, or execute the tool's handler callable
    # based on whether the HTTP request is a GET or a POST
    form = mod.HandlerForm(request.form)
    if request.method == 'POST' and form.validate():
        converters = {
            'application/json': renderers.render_json,
            'application/xml':  renderers.render_xml,
            'text/html':        renderers.render_html,
            }
        mimetype = request.accept_mimetypes.best_match(converters.keys())
        result = mod.handler(**form.data)
        dimensions = result.pop('dimensions')
        result = converters[mimetype](result, dimensions=dimensions)
        # If we're generating HTML, wrap the result in a template
        if mimetype == 'text/html':
            result = render_template(
                'result.html',
                title=mod.__doc__,
                result=result)
        response = make_response(result)
        response.mimetype = mimetype
        return response
    return render_template(
        '%s.html' % name,
        title=mod.__doc__,
        form=form,
        )


def main():
    app.run(
        host='0.0.0.0',
        debug=True
        )
