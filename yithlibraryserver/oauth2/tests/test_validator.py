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

import base64
import datetime
import os

from bson.tz_util import utc

from oauthlib.common import Request, to_unicode

from yithlibraryserver import testing
from yithlibraryserver.datetimeservice.testing import FakeDatetimeService
from yithlibraryserver.oauth2.validator import RequestValidator


class RequestValidatorTests(testing.TestCase):

    clean_collections = ('applications', 'users', 'authorization_codes',
                         'access_codes')

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
        self.user_id = self.db.users.insert({
            'twitter_id': 'twitter1',
            'screen_name': 'JohnDoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
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

    def test_save_authorization_code(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'

        rv, request = self._create_request_validator()
        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)
        auth_code = self.db.authorization_codes.find_one({'code': 'abcdef'})
        self.assertEquals(auth_code['user'], self.user_id)
        self.assertEquals(auth_code['client_id'], '123456')
        self.assertEquals(auth_code['scope'], 'read-passwords write-passwords')
        self.assertEquals(auth_code['redirect_uri'],
                          'https://example.com/callback')
        expected_expiration = datetime.datetime(2012, 1, 10, 15, 31, 11,
                                                tzinfo=utc)
        expected_expiration += datetime.timedelta(minutes=10)
        self.assertEquals(auth_code['expiration'], expected_expiration)

        del os.environ['YITH_FAKE_DATETIME']

    def test_authenticate_client_no_headers_no_request_attrs(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_no_headers_bad_request_attrs(self):
        rv, request = self._create_request_validator()
        request.client_id = 'bad client id'
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_no_headers_bad_client_secret(self):
        rv, request = self._create_request_validator()
        request.client_id = '123456'
        request.client_secret = 'secret'
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_no_headers_good_request_attrs(self):
        rv, request = self._create_request_validator()
        request.client_id = '123456'
        request.client_secret = 's3cr3t'
        self.assertTrue(rv.authenticate_client(request))

    def test_authenticate_client_headers_bad_type(self):
        rv, request = self._create_request_validator()
        request.headers['Authorization'] = 'Bearer 123456789'
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_headers_bad_client_id(self):
        rv, request = self._create_request_validator()
        data = 'bad-client-id:bad-password'.encode('utf-8')
        auth = to_unicode(base64.b64encode(data), 'utf-8')
        request.headers['Authorization'] = 'Basic ' + auth
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_headers_bad_password(self):
        rv, request = self._create_request_validator()
        auth = to_unicode(base64.b64encode('123456:secret'.encode('utf-8')),
                          'utf-8')
        request.headers['Authorization'] = 'Basic ' + auth
        self.assertFalse(rv.authenticate_client(request))

    def test_authenticate_client_headers_good(self):
        rv, request = self._create_request_validator()
        auth = to_unicode(base64.b64encode('123456:s3cr3t'.encode('utf-8')),
                          'utf-8')
        request.headers['Authorization'] = 'Basic ' + auth
        self.assertTrue(rv.authenticate_client(request))

    def test_authenticate_client_id_non_implemented(self):
        rv, request = self._create_request_validator()
        self.assertRaises(NotImplementedError, rv.authenticate_client_id,
                          '123456', request)

    def test_validate_code_bad_code(self):
        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertFalse(rv.validate_code('123456', 'abcdef', client, request))

    def test_validate_code_expired_code(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'

        rv, request = self._create_request_validator()
        client = rv.get_client('123456')

        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)

        # move time forward 11 minutes
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-42-11'

        self.assertFalse(rv.validate_code('123456', 'abcdef', client, request))
        del os.environ['YITH_FAKE_DATETIME']

    def test_validate_code_good(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'

        rv, request = self._create_request_validator()
        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)

        # move time forward 5 minutes
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-36-11'

        rv2, request2 = self._create_request_validator()
        client2 = rv2.get_client('123456')
        self.assertTrue(rv2.validate_code('123456', 'abcdef', client2, request2))
        self.assertEquals(request2.user, self.user_id)
        self.assertEquals(request2.scopes, ['read-passwords', 'write-passwords'])

        del os.environ['YITH_FAKE_DATETIME']

    def test_confirm_redirect_uri_no_redirect_uri(self):
        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertTrue(rv.confirm_redirect_uri('123456', 'abcdef',
                                                None, client))

    def test_confirm_redirect_uri_bad_code(self):
        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertFalse(rv.confirm_redirect_uri('123456', 'abcdef',
                                                 'https://example.com/callback',
                                                 client))

    def test_confirm_redirect_uri_bad_redirect_uri(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)

        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertFalse(rv.confirm_redirect_uri('123456', 'abcdef',
                                                 'http://example.com/callback',
                                                 client))
        del os.environ['YITH_FAKE_DATETIME']

    def test_confirm_redirect_uri_good_redirect_uri(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)

        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertTrue(rv.confirm_redirect_uri('123456', 'abcdef',
                                                'https://example.com/callback',
                                                client))
        del os.environ['YITH_FAKE_DATETIME']

    def test_validate_grant_type_bad(self):
        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertFalse(rv.validate_grant_type('123456', 'bad-code',
                                                client, request))

    def test_validate_grant_type_good(self):
        rv, request = self._create_request_validator()
        client = rv.get_client('123456')
        self.assertTrue(rv.validate_grant_type('123456', 'authorization_code',
                                               client, request))

    def test_save_bearer_token(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        token = {
            'expires_in': 3600,  # seconds
            'access_token': 'fghijk',
            'token_type': 'Bearer',
            'refresh_token': 'lmnopq',
        }
        request.user = self.user_id
        request.scopes = ['read-passwords', 'write-passwords']
        request.client = rv.get_client('123456')
        rv.save_bearer_token(token, request)

        access_code = self.db.access_codes.find_one({'access_token': 'fghijk'})
        self.assertEquals(access_code['access_token'], 'fghijk')
        self.assertEquals(access_code['type'], 'Bearer')
        self.assertEquals(access_code['scope'], 'read-passwords write-passwords')
        self.assertEquals(access_code['refresh_token'], 'lmnopq')
        expected_expiration = datetime.datetime(2012, 1, 10, 15, 31, 11,
                                                tzinfo=utc)
        expected_expiration += datetime.timedelta(seconds=3600)
        self.assertEquals(access_code['expiration'], expected_expiration)
        self.assertEquals(access_code['user_id'], self.user_id)
        self.assertEquals(access_code['client_id'], '123456')

        del os.environ['YITH_FAKE_DATETIME']

    def test_invalidate_authorization_code(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'

        rv, request = self._create_request_validator()
        request.user = {'_id': self.user_id}
        request.scopes = ['read-passwords', 'write-passwords']
        request.redirect_uri = 'https://example.com/callback'
        rv.save_authorization_code('123456', {'code': 'abcdef'}, request)

        del os.environ['YITH_FAKE_DATETIME']

        rv, request = self._create_request_validator()
        request.client = rv.get_client('123456')
        rv.invalidate_authorization_code('123456', 'abcdef', request)
        auth_code = self.db.authorization_codes.find_one({'code': 'abcdef'})
        self.assertEquals(auth_code, None)

    def test_validate_bearer_token_no_token(self):
        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_bearer_token(
            'fghijk',
            ['read-passwords', 'write-passwords'],
            request,
        ))

    def test_validate_bearer_token_expired_token(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        token = {
            'expires_in': 3600,  # seconds
            'access_token': 'fghijk',
            'token_type': 'Bearer',
            'refresh_token': 'lmnopq',
        }
        request.user = self.user_id
        request.scopes = ['read-passwords', 'write-passwords']
        request.client = rv.get_client('123456')
        rv.save_bearer_token(token, request)

        # move time forward 2 hours
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-17-42-11'

        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_bearer_token(
            'fghijk',
            ['read-passwords', 'write-passwords'],
            request,
        ))

        del os.environ['YITH_FAKE_DATETIME']

    def test_validate_bearer_token_bad_scopes(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        token = {
            'expires_in': 3600,  # seconds
            'access_token': 'fghijk',
            'token_type': 'Bearer',
            'refresh_token': 'lmnopq',
        }
        request.user = self.user_id
        request.scopes = ['read-passwords', 'write-passwords']
        request.client = rv.get_client('123456')
        rv.save_bearer_token(token, request)

        # move time forward 1/2 hour
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-16-01-11'

        rv, request = self._create_request_validator()
        self.assertFalse(rv.validate_bearer_token(
            'fghijk',
            ['read-passwords', 'write-passwords', 'read-userinfo'],
            request,
        ))

        del os.environ['YITH_FAKE_DATETIME']

    def test_validate_bearer_token_good(self):
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-15-31-11'
        rv, request = self._create_request_validator()
        token = {
            'expires_in': 3600,  # seconds
            'access_token': 'fghijk',
            'token_type': 'Bearer',
            'refresh_token': 'lmnopq',
        }
        request.user = self.user_id
        request.scopes = ['read-passwords', 'write-passwords']
        request.client = rv.get_client('123456')
        rv.save_bearer_token(token, request)

        # move time forward 1/2 hour
        os.environ['YITH_FAKE_DATETIME'] = '2012-1-10-16-01-11'

        rv, request = self._create_request_validator()
        self.assertTrue(rv.validate_bearer_token(
            'fghijk',
            ['read-passwords', 'write-passwords'],
            request,
        ))

        del os.environ['YITH_FAKE_DATETIME']

    def test_get_original_scopes_non_implemented(self):
        rv, request = self._create_request_validator()
        self.assertRaises(NotImplementedError, rv.get_original_scopes,
                          'refresh-token', request)
