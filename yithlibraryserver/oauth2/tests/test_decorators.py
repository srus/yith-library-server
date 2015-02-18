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

import datetime

from bson.tz_util import utc
from freezegun import freeze_time

from pyramid.httpexceptions import HTTPUnauthorized

from yithlibraryserver import testing
from yithlibraryserver.oauth2.decorators import (
    protected,
    protected_method,
)


@protected(['scope1'])
def view_function(request):
    return 'response'


class ViewClass(object):

    def __init__(self, request):
        self.request = request

    @protected_method(['scope1'])
    def view_method(self):
        return 'response'


class DecoratorsTests(testing.TestCase):

    def setUp(self):
        super(DecoratorsTests, self).setUp()
        self.user_id = self.db.users.insert({
            'username': 'user1',
        })

    def _create_access_code(self, scope):
        expiration = datetime.datetime(2014, 2, 23, 9, 0, tzinfo=utc)
        self.db.access_codes.insert({
            'access_token': '1234',
            'type': 'Bearer',
            'expiration': expiration,
            'user_id': self.user_id,
            'scope': scope,
            'client_id': 'client1',
        })

    @freeze_time('2014-02-23 08:00:00')
    def test_protected_bad_scope(self):
        self._create_access_code('scope2')

        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)

        self.assertRaises(HTTPUnauthorized, view_function, request)

    @freeze_time('2014-02-23 08:00:00')
    def test_protected(self):
        self._create_access_code('scope1')

        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)

        self.assertEqual(view_function(request), 'response')
        self.assertEqual(request.user['username'], 'user1')

    @freeze_time('2014-02-23 08:00:00')
    def test_protected_method_bad_scope(self):
        self._create_access_code('scope2')
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)

        view_object = ViewClass(request)
        self.assertRaises(HTTPUnauthorized, view_object.view_method)

    @freeze_time('2014-02-23 08:00:00')
    def test_protected_method(self):
        self._create_access_code('scope1')
        request = testing.FakeRequest(headers={
            'Authorization': 'Bearer 1234',
        }, db=self.db)

        view_object = ViewClass(request)
        self.assertEqual(view_object.view_method(), 'response')
        self.assertEqual(request.user['username'], 'user1')
