# Yith Library Server is a password storage server.
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

import unittest

from yithlibraryserver import testing
from yithlibraryserver.compat import text_type
from yithlibraryserver.db import DBSession
from yithlibraryserver.user.models import User


class FullNameTests(unittest.TestCase):

    def test_empty(self):
        user = User(first_name='', last_name='')
        self.assertEqual(user.full_name, '')

    def test_only_first_name(self):
        user = User(first_name='John', last_name='')
        self.assertEqual(user.full_name, 'John')

    def test_only_last_name(self):
        user = User(first_name='', last_name='Doe')
        self.assertEqual(user.full_name, 'Doe')

    def test_first_and_last_name(self):
        user = User(first_name='John', last_name='Doe')
        self.assertEqual(user.full_name, 'John Doe')


class UnicodeTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('yithlibraryserver.user')

    def tearDown(self):
        testing.tearDown()

    def test_unicode_only_id(self):
        user = User()
        DBSession.add(user)
        DBSession.flush()
        self.assertEqual(text_type(user), text_type(user.id))

    def test_unicode_only_email(self):
        user = User(email='john@example.com')
        DBSession.add(user)
        DBSession.flush()
        self.assertEqual(text_type(user), 'john@example.com')

    def test_unicode_only_last_name(self):
        user = User(last_name='Doe')
        DBSession.add(user)
        DBSession.flush()
        self.assertEqual(text_type(user), 'Doe')

    def test_unicode_first_name_and_last_name(self):
        user = User(first_name='John', last_name='Doe')
        DBSession.add(user)
        DBSession.flush()
        self.assertEqual(text_type(user), 'John Doe')

    def test_unicode_only_screen_name(self):
        user = User(screen_name='Johnny')
        DBSession.add(user)
        DBSession.flush()
        self.assertEqual(text_type(user), 'Johnny')

    def test_unicode_is_str(self):
        u = User()
        DBSession.add(u)
        DBSession.flush()
        self.assertEqual(u.__unicode__(), u.__str__())


class UpdatePreferencesTests(unittest.TestCase):

    def setUp(self):
        self.user = User(allow_google_analytics=False,
                         send_passwords_periodically=True)

    def test_empty_preferences(self):
        self.user.update_preferences({})
        self.assertEqual(self.user.allow_google_analytics, False)
        self.assertEqual(self.user.send_passwords_periodically, True)

    def test_fake_preferences(self):
        self.user.update_preferences({'foo': 'bar'})
        self.assertEqual(self.user.allow_google_analytics, False)
        self.assertEqual(self.user.send_passwords_periodically, True)

    def test_real_preferences(self):
        self.user.update_preferences({
            'allow_google_analytics': True,
            'send_passwords_periodically': False,
        })
        self.assertEqual(self.user.allow_google_analytics, True)
        self.assertEqual(self.user.send_passwords_periodically, False)
