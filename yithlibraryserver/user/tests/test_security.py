# Yith Library Server is a password storage server.
# Copyright (C) 2012-2013 Yaco Sistemas
# Copyright (C) 2012-2013 Alejandro Blanco Escudero <alejandro.b.e@gmail.com>
# Copyright (C) 2012-2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

from pyramid import testing
from pyramid.httpexceptions import HTTPFound

from pyramid_sqlalchemy import Session

from yithlibraryserver.testing import DatabaseTestCase
from yithlibraryserver.user.security import (
    get_user,
    assert_authenticated_user_is_registered,
)
from yithlibraryserver.user.models import User


class GetUserTests(DatabaseTestCase):

    def setUp(self):
        super(GetUserTests, self).setUp()
        self.config = testing.setUp()
        self.config.include('yithlibraryserver.user')

    def tearDown(self):
        testing.tearDown()
        super(GetUserTests, self).tearDown()

    def test_get_user_no_userid(self):
        request = testing.DummyRequest()
        self.assertEqual(None, get_user(request))

    def test_get_user_no_user(self):
        request = testing.DummyRequest()
        self.config.testing_securitypolicy(userid=123)
        self.assertEqual(None, get_user(request))

    def test_get_user_existing_user(self):
        user = User(screen_name='John Doe')
        Session.add(user)
        Session.flush()
        user_id = user.id

        self.config.testing_securitypolicy(userid=user_id)
        request = testing.DummyRequest()
        new_user = get_user(request)
        self.assertEqual(new_user.id, user.id)
        self.assertEqual(new_user.screen_name, 'John Doe')


class AssertAuthenticatedUserIsRegisteredTests(DatabaseTestCase):

    def setUp(self):
        super(AssertAuthenticatedUserIsRegisteredTests, self).setUp()
        self.config = testing.setUp()
        self.config.include('yithlibraryserver.user')

    def tearDown(self):
        testing.tearDown()
        super(AssertAuthenticatedUserIsRegisteredTests, self).tearDown()

    def test_assert_authenticated_user_is_registered_no_user(self):
        self.config.testing_securitypolicy(userid=1)

        request = testing.DummyRequest()

        self.assertRaises(HTTPFound, assert_authenticated_user_is_registered, request)
        try:
            assert_authenticated_user_is_registered(request)
        except HTTPFound as exp:
            self.assertEqual(exp.location, '/register')

    def test_assert_authenticated_user_is_registered_existing_user(self):
        user = User(screen_name='John Doe')
        Session.add(user)
        Session.flush()
        user_id = user.id

        self.config.testing_securitypolicy(userid=user_id)
        request = testing.DummyRequest()
        res = assert_authenticated_user_is_registered(request)
        self.assertEqual(res.id, user_id)
        self.assertEqual(res.screen_name, 'John Doe')
