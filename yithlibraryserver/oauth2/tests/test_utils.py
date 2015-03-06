# Yith Library Server is a password storage server.
# Copyright (C) 2014 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
#
# This file is part of Yith Library Server.
#
# Yith Library Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Yith Library Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Yith Library Server.  If not, see <http://www.gnu.org/licenses/>.

import unittest

from webob.compat import native_

from pyramid import testing

from yithlibraryserver.oauth2.utils import (
    create_response,
    decode_base64,
    extract_params,
    response_from_error,
)


class Error(object):

    def __init__(self, error):
        self.error = error


class ExtractParamsTests(unittest.TestCase):

    def test_extract_params(self):
        request = testing.DummyRequest(headers={
            'wsgi.input': 'foo',
            'wsgi.errors': 'none',
        })
        request.body = 'loren ipsum'
        request.url = 'http://example.com/foo/bar'
        uri, method, body, headers = extract_params(request)
        self.assertEqual(uri, 'http://example.com/foo/bar')
        self.assertEqual(method, 'GET')
        self.assertEqual(body, 'loren ipsum')
        self.assertEqual(headers, {})

    def test_create_response(self):
        response = create_response({'Content-Type': 'text/html'}, 'body', 200)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.headers[native_('Content-Type')],
                         native_('text/html'))
        self.assertEqual(response.body, 'body'.encode('utf-8'))

    def test_response_from_error(self):
        response = response_from_error(Error('testing error'))
        self.assertEqual(response.status, '400 Bad Request')
        expected = 'Evil client is unable to send a proper request. Error is: testing error'
        self.assertEqual(response.body, expected.encode('utf-8'))

    def test_decode_base64(self):
        self.assertEqual('foobar', decode_base64('Zm9vYmFy'))
