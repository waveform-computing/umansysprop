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

"""An online system for calculating the properties of individual organic
molecules and ensemble mixtures"""

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

from flask import Flask, request, jsonify, render_template, url_for, flash

from . import tools

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(
        'index.html',
        tools=[
            finder.find_module(modname).load_module(modname)
            for (finder, modname, ispkg) in pkgutil.iter_modules(
                tools.__path__, prefix=tools.__name__ + '.')
            if not ispkg and modname != 'template'
            ]
        )

@app.route('/tool/<name>', methods=['GET', 'POST'])
def tool(name):
    mod_name = '%s.%s' % (tools.__name__, name)
    if request.method == 'GET':
        return render_template(
            '%s.html' % name,
            tool=sys.modules[mod_name]
            )
    elif request.method == 'POST':
        try:
            mod = sys.modules[mod_name]
        except KeyError:
            loader = pkgutil.get_loader(mod_name)
            mod = loader.load_module(mod_name)
        assert hasattr(mod, 'handle')
        args = {
            k: v if len(v) > 1 else v[0]
            for (k, v) in request.form.iterlists()
            if k != 'submit'
            }
        return jsonify(mod.handle(**args))

def main():
    app.run(
        host='0.0.0.0',
        debug=True
        )
