# Yith Library Server is a password storage server.
# Copyright (C) 2012-2014 Yaco Sistemas
# Copyright (C) 2012-2014 Alejandro Blanco Escudero <alejandro.b.e@gmail.com>
# Copyright (C) 2012-2014 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

import datetime
import os

from bson.tz_util import utc

from pyramid.httpexceptions import HTTPUnauthorized

from yithlibraryserver import testing
from yithlibraryserver.oauth2.authorization import (
    Authorizator,
    verify_request,
)


class AuthorizatorTests(testing.TestCase):

    clean_collections = ('authorized_apps', 'users')

    def setUp(self):
        super(AuthorizatorTests, self).setUp()
        self.authorizator = Authorizator(self.db)

    def test_is_app_authorized_no_authorized_apps(self):
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        }))

    def test_is_app_authorized_different_client_id(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 2,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        }))

    def test_is_app_authorized_different_user(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 2},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        }))

    def test_is_app_authorized_different_redirect_uri(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback-new',
            'response_type': 'code',
        }))

    def test_is_app_authorized_different_response_type(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'token',
        }))

    def test_is_app_authorized_different_scopes(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertFalse(self.authorizator.is_app_authorized([
            'scope1', 'scope2', 'scope3',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        }))

    def test_is_app_authorized_everything_equal(self):
        self.db.authorized_apps.insert({
            'client_id': 1,
            'user': 1,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1 scope2',
        })
        self.assertTrue(self.authorizator.is_app_authorized([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        }))

    def test_store_user_authorization_no_previous_authorization(self):
        self.assertEqual(self.db.authorized_apps.count(), 0)
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        self.assertEqual(self.db.authorized_apps.count(), 1)

    def test_store_user_authorization_previous_authorization(self):
        self.assertEqual(self.db.authorized_apps.count(), 0)
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        self.assertEqual(self.db.authorized_apps.count(), 1)

        # Store the same authorization again
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        # still only one record
        self.assertEqual(self.db.authorized_apps.count(), 1)

    def test_get_user_authorizations_empty(self):
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 0)

    def test_get_user_authorizations_one_authorization(self):
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 1)
        self.assertEqual(auths[0]['client_id'], 1)
        self.assertEqual(auths[0]['redirect_uri'], 'http://example.com/callback')
        self.assertEqual(auths[0]['response_type'], 'code')
        self.assertEqual(auths[0]['scope'], 'scope1 scope2')

    def test_get_user_authorizations_two_authorization(self):
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 2,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback2',
            'response_type': 'code',
        })
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 2,
            'user': {'_id': 2},
            'redirect_uri': 'http://example.com/callback2',
            'response_type': 'code',
        })
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 2)
        self.assertEqual(auths[0]['client_id'], 1)
        self.assertEqual(auths[0]['redirect_uri'], 'http://example.com/callback')
        self.assertEqual(auths[0]['response_type'], 'code')
        self.assertEqual(auths[0]['scope'], 'scope1 scope2')

        self.assertEqual(auths[1]['client_id'], 2)
        self.assertEqual(auths[1]['redirect_uri'], 'http://example.com/callback2')
        self.assertEqual(auths[1]['response_type'], 'code')
        self.assertEqual(auths[1]['scope'], 'scope1 scope2')

    def test_remove_user_authorization(self):
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 0)
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
        })
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 1)
        self.authorizator.remove_user_authorization({'_id': 1}, 1)
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 0)

    def test_remove_all_user_authorizations(self):
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 0)
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 1,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback/1',
            'response_type': 'code',
        })
        self.authorizator.store_user_authorization([
            'scope1', 'scope2',
        ], {
            'client_id': 2,
            'user': {'_id': 1},
            'redirect_uri': 'http://example.com/callback/2',
            'response_type': 'code',
        })
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 2)
        self.authorizator.remove_all_user_authorizations({'_id': 1})
        auths = self.authorizator.get_user_authorizations({'_id': 1})
        self.assertEqual(auths.count(), 0)


class VerifyRequestTests(testing.TestCase):

    clean_collections = ('access_codes', 'users')

    def test_no_auth_header(self):
        request = testing.FakeRequest(headers={}, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope1'])

    def test_basic_auth_header(self):
        request = testing.FakeRequest(headers={
            'Authorization': 'Basic foobar',
        }, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope1'])

    def test_bad_bearer_header(self):
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope1'])

    def test_invalid_scope(self):
        os.environ['YITH_FAKE_DATETIME'] = '2014-2-23-08-00-00'
        expiration = datetime.datetime(2014, 2, 23, 9, 0, tzinfo=utc)
        self.db.access_codes.insert({
            'access_token': '1234',
            'type': 'Bearer',
            'expiration': expiration,
            'user_id': 'user1',
            'scope': 'scope1',
            'client_id': 'client1',
        })
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope2'])

        del os.environ['YITH_FAKE_DATETIME']

    def test_expired_token(self):
        os.environ['YITH_FAKE_DATETIME'] = '2014-2-23-08-00-00'
        expiration = datetime.datetime(2014, 2, 23, 7, 0, tzinfo=utc)
        self.db.access_codes.insert({
            'access_token': '1234',
            'type': 'Bearer',
            'expiration': expiration,
            'user_id': 'user1',
            'scope': 'scope1',
            'client_id': 'client1',
        })
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope1'])

        del os.environ['YITH_FAKE_DATETIME']

    def test_invalid_user(self):
        os.environ['YITH_FAKE_DATETIME'] = '2014-2-23-08-00-00'
        expiration = datetime.datetime(2014, 2, 23, 9, 0, tzinfo=utc)
        self.db.access_codes.insert({
            'access_token': '1234',
            'type': 'Bearer',
            'expiration': expiration,
            'user_id': 'user1',
            'scope': 'scope1',
            'client_id': 'client1',
        })
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)
        self.assertRaises(HTTPUnauthorized, verify_request, request, ['scope1'])

        del os.environ['YITH_FAKE_DATETIME']

    def test_valid_user(self):
        os.environ['YITH_FAKE_DATETIME'] = '2014-2-23-08-00-00'

        user_id = self.db.users.insert({
                'username': 'user1',
                })

        expiration = datetime.datetime(2014, 2, 23, 9, 0, tzinfo=utc)
        self.db.access_codes.insert({
            'access_token': '1234',
            'type': 'Bearer',
            'expiration': expiration,
            'user_id': user_id,
            'scope': 'scope1',
            'client_id': 'client1',
        })
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)

        user = verify_request(request, ['scope1'])
        self.assertEqual(user['username'], 'user1')

        del os.environ['YITH_FAKE_DATETIME']
