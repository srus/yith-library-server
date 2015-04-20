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

import unittest

from freezegun import freeze_time

from pyramid import testing

from pyramid_sqlalchemy import metadata
from pyramid_sqlalchemy import Session

from yithlibraryserver.testing import (
    get_test_db_uri,
    sqlalchemy_setup,
    sqlalchemy_teardown,
)
from yithlibraryserver.user.analytics import GoogleAnalytics
from yithlibraryserver.user.analytics import USER_ATTR
from yithlibraryserver.user.models import User
from yithlibraryserver.user.utils import split_name
from yithlibraryserver.user.utils import register_or_update


class SplitNameTests(unittest.TestCase):

    def test_split_name_two_words(self):
        self.assertEqual(split_name('John Doe'), ('John', 'Doe'))

    def test_split_name_one_word(self):
        self.assertEqual(split_name('John'), ('John', ''))

    def test_split_name_three_words(self):
        self.assertEqual(split_name('John M Doe'), ('John', 'M Doe'))

    def test_split_name_empty_string(self):
        self.assertEqual(split_name(''), ('', ''))


class RegisterOrUpdateTests(unittest.TestCase):

    def setUp(self):
        self.db_uri = get_test_db_uri()
        self.db_context = sqlalchemy_setup(self.db_uri)

        self.config = testing.setUp()
        self.config.include('yithlibraryserver.user')

        metadata.create_all()

    def tearDown(self):
        testing.tearDown()
        sqlalchemy_teardown(self.db_context)

    # def test_update_user(self):
    #     user_id = self.db.users.insert({
    #         'screen_name': 'John Doe',
    #         'first_name': 'John',
    #         'last_name': '',
    #     })
    #     user = self.db.users.find_one({'_id': user_id})
    #     update_user(self.db, user, {}, {})

    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     # the user has not changed
    #     self.assertEqual(updated_user['screen_name'], user['screen_name'])
    #     self.assertEqual(updated_user['first_name'], user['first_name'])
    #     self.assertEqual(updated_user['last_name'], user['last_name'])

    #     # update the last_name
    #     update_user(self.db, user, {'last_name': 'Doe'}, {})
    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     self.assertEqual(updated_user['last_name'], 'Doe')

    #     # add an email attribute
    #     update_user(self.db, user, {'email': 'john@example.com'}, {})
    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     self.assertEqual(updated_user['email'], 'john@example.com')

    #     # if an attribute has no value, no update happens
    #     update_user(self.db, user, {'first_name': ''}, {})
    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     self.assertEqual(updated_user['first_name'], 'John')

    #     # update a non existing attribute
    #     update_user(self.db, user, {'foo': 'bar'}, {})
    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     self.assertFalse('foo' in updated_user)

    #     # update the same attribute within the last parameter
    #     update_user(self.db, user, {}, {'foo': 'bar'})
    #     updated_user = self.db.users.find_one({'_id': user_id})
    #     self.assertEqual(updated_user['foo'], 'bar')

    @freeze_time('2013-01-02 10:11:12')
    def test_register_or_update_new_user(self):
        request = testing.DummyRequest()
        request.session = {}
        request.google_analytics = GoogleAnalytics(request)
        response = register_or_update(request, 'twitter', '1', {
            'screen_name': 'JohnDoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'invented_attribute': 'foo',  # this will not be in the output
        }, '/next')
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, '/register')
        self.assertEqual(request.session['next_url'], '/next')
        self.assertEqual(request.session['user_info'], {
            'screen_name': 'JohnDoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': '',
            'provider': 'twitter',
            'twitter_id': '1',
        })

    @freeze_time('2013-01-02 10:11:12')
    def test_register_or_update_existing_user(self):
        user = User(twitter_id='1',
                    screen_name='JohnDoe',
                    first_name='John',
                    last_name='')
        Session.add(user)
        Session.flush()
        user_id = user.id

        request = testing.DummyRequest()
        request.session = {USER_ATTR: True}
        request.google_analytics = GoogleAnalytics(request)
        response = register_or_update(request, 'twitter', '1', {
            'screen_name': 'JohnDoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
        }, '/next')
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, '/next')
        user = Session.query(User).filter(User.id==user_id).one()
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.allow_google_analytics, True)

    @freeze_time('2013-01-02 10:11:12')
    def test_register_or_update_next_url_in_session(self):
        user = User(twitter_id='1',
                    screen_name='JohnDoe',
                    first_name='John',
                    last_name='')
        Session.add(user)
        Session.flush()

        request = testing.DummyRequest()
        request.session = {'next_url': '/foo'}
        request.google_analytics = GoogleAnalytics(request)
        response = register_or_update(request, 'twitter', '1', {
            'screen_name': 'JohnDoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
        }, '/next')
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, '/foo')
