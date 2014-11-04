# Yith Library Server is a password storage server.
# Copyright (C) 2012-2013 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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
from pyramid import testing
from pyramid.events import NewRequest
from pyramid.request import Request

from yithlibraryserver.subscribers import add_compress_response_callback


class ContentEncodingTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _request(self, headers=None):
        if headers is None:
            request = Request({})
        else:
            request = Request({}, headers=headers)

        request.registry = self.config.registry
        event = NewRequest(request)
        add_compress_response_callback(event)

        response = request.response
        request._process_response_callbacks(response)
        return response

    def test_no_compression(self):
        response = self._request()
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_encoding, None)

    def test_identity_compression(self):
        response = self._request({'Accept-Encoding': 'identity'})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_encoding, None)

    def test_gzip_compression(self):
        response = self._request({'Accept-Encoding': 'gzip'})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_encoding, 'gzip')
