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
Client library for the UManSysProp server; an online framework for calculating
the properties of individual organic molecules and ensemble mixtures
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')


import types
import json
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests


class UManSysProp(object):

    _method_template = """\
def {method_name}(self, {method_params}):
    return self._json_rpc("{method_name}", {method_call})
"""

    def __init__(self, base_url='http://umansysprop.seaes.manchester.ac.uk/'):
        self._base_url = base_url
        response = requests.get(urljoin(self._base_url, 'api'), headers={
            'Accept': 'application/json'})
        response.raise_for_status()
        for name, props in response.json().items():
            # Construct a dynamic method for each function that the API
            # defines.  The method will take the parameters specified by the
            # API, and will have a doc-string also specified by the API
            method_definition = self._method_template.format(
                    method_name=name,
                    method_params=', '.join(props['params']),
                    method_call=', '.join(
                        '%s=%s' % (param, param) for param in props['params'])
                    )
            l = {}
            exec(method_definition, globals(), l)
            f = l[name]
            f.__doc__ = props['doc']
            setattr(self, name, types.MethodType(f, self))

    def _json_rpc(self, name, **params):
        response = requests.post(
                urljoin(self._base_url, 'api/%s' % name),
                data=json.dumps(params),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    })
        response.raise_for_status()
        return response.json()['result']

