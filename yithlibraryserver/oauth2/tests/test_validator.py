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

from oauthlib.common import Request

from yithlibraryserver import testing
from yithlibraryserver.datetimeservice.testing import FakeDatetimeService
from yithlibraryserver.oauth2.validator import RequestValidator


class RequestValidatorTests(testing.TestCase):

    clean_collections = ('applications', 'users')

    def setUp(self):
        super(RequestValidatorTests, self).setUp()
        self.owner_id = self.db.users.insert({
            'twitter_id': 'twitter2',
            'screen_name': 'Administrator',
            'first_name': 'Alice',
            'last_name': 'Doe',
            'email': 'alice@example.com',
        })
        self.app_id = self.db.applications.insert({
            'owner': self.owner_id,
            'client_id': '123456',
            'client_secret': 's3cr3t',
            'name': 'Example',
            'main_url': 'https://example.com',
            'callback_url': 'https://example.com/callback',
            'image_url': 'https://example.com/logo.png',
            'description': 'Example description',
        })

    def _create_request_validator(self, scopes=None):
        rv = RequestValidator(self.db,
                              FakeDatetimeService(None),
                              default_scopes=scopes)
        request = Request('https://server.example.com/')
        return rv, request

    def test_init(self):
        rv, _ = self._create_request_validator()
        self.assertEqual(rv.default_scopes, ['read-passwords'])

    def test_init_custom_default_scopes(self):
        rv, _ = self._create_request_validator(['scope1', 'scope2'])
        self.assertEqual(rv.default_scopes, ['scope1', 'scope2'])

    def test_get_client(self):
        rv, _ = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertEqual(client.owner, self.owner_id)
        self.assertEqual(client.client_id, '123456')
        self.assertEqual(client.client_secret, 's3cr3t')
        self.assertEqual(client.name, 'Example')
        self.assertEqual(client.callback_url, 'https://example.com/callback')

    def test_get_pretty_scopes(self):
        rv, _ = self._create_request_validator()
        self.assertEqual(rv.get_pretty_scopes([
            'read-passwords',
            'write-passwords',
            'read-userinfo',
        ]), [
            'Access your passwords',
            'Modify your passwords',
            'Access your user information',
        ])

    def test_validate_client_id_true(self):
        rv, request = self._create_request_validator()
        self.assertTrue(rv.validate_client_id('123456', request))
        self.assertEqual(request.client.client_id, '123456')

    def test_validate_client_id_false(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_client_id('invalid-client-id', request))
        self.assertEqual(request.client, None)

    def test_validate_redirect_uri_true(self):
        rv, request = self._create_request_validator()
        self.assertTrue(rv.validate_redirect_uri(
            '123456', 'https://example.com/callback', request))

    def test_validate_redirect_uri_false(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_redirect_uri(
            '123456', 'https://phising.example.com/callback', request))

    def test_get_default_redirect_uri(self):
        rv, request = self._create_request_validator()
        self.assertEquals(rv.get_default_redirect_uri('123456', request),
                          'https://example.com/callback')

    def test_validate_scopes_true(self):
        rv, request = self._create_request_validator()
        self.assertTrue(rv.validate_scopes(
            '123456',
            ['read-passwords'],
            None, request,
        ))
        self.assertTrue(rv.validate_scopes(
            '123456',
            ['read-passwords', 'write-passwords'],
            None, request,
        ))
        self.assertTrue(rv.validate_scopes(
            '123456',
            ['read-passwords', 'write-passwords', 'read-userinfo'],
            None, request,
        ))

    def test_validate_scopes_false(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_scopes(
            '123456',
            ['read-userinfo', 'write-userinfo'],
            None, request,
        ))

    def test_get_default_scopes(self):
        rv, request = self._create_request_validator()
        self.assertEquals(rv.get_default_scopes('123456', request),
                          ['read-passwords'])

    def test_validate_response_type_true(self):
        rv, request = self._create_request_validator()
        self.assertTrue(rv.validate_response_type('123456', 'code',
                                                  None, request))

    def test_validate_response_type_false(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_response_type('123456', 'token',
                                                   None, request))
