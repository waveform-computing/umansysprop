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
=============================
``umansysprop.client`` Module
=============================

This module contains the client library for interacting with the UManSysProp
server. Only one user-accessible class is defined in the module:

UManSysProp
===========

.. autoclass:: UManSysProp

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

from . import results


class UManSysProp(object):

    _method_template = """\
def {name}(self, {params}):
    return self._json_rpc("{url}", {call})
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
                    name=name,
                    url=props['url'],
                    params=', '.join(props['params']),
                    call=', '.join(
                        '%s=%s' % (param, param) for param in props['params'])
                    )
            l = {}
            exec(method_definition, globals(), l)
            f = l[name]
            f.__doc__ = props['doc']
            setattr(self, name, types.MethodType(f, self))

    def _json_rpc(self, url, **params):
        response = requests.post(
                urljoin(self._base_url, url),
                data=json.dumps(params),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    })
        if 400 <= response.status_code < 500:
            # Some kind of client error; try and decode the body as JSON to
            # determine the details and raise a reasonable exception
            exc_type = response.json()['exc_type']
            exc_value = response.json()['exc_value']
            # Only permit a specific set of exceptions
            exc_class = {
                'ValueError':   ValueError,
                'NameError':    NameError,
                'KeyError':     KeyError,
                }[exc_type]
            if isinstance(exc_value, str):
                raise exc_class(exc_value)
            else:
                raise exc_class(*exc_value)
        elif response.status_code >= 500:
            import pdb; pdb.set_trace()
            raise RuntimeError('Server error: %s' % response.body)
        else:
            response.raise_for_status()
        return results.Result.from_json(response.json())

