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

import unittest

from pyramid import testing
from pyramid.testing import DummyRequest

from pyramid_mailer import get_mailer

from yithlibraryserver.db import MongoDB
from yithlibraryserver.user.accounts import get_available_providers
from yithlibraryserver.user.accounts import get_providers, get_n_passwords
from yithlibraryserver.user.accounts import get_accounts, merge_accounts
from yithlibraryserver.user.accounts import merge_users
from yithlibraryserver.user.accounts import notify_admins_of_account_removal
from yithlibraryserver.testing import MONGO_URI, TestCase


class AccountTests(TestCase):

    clean_collections = ('users', 'passwords')

    def test_get_available_providers(self):
        self.assertEqual(('facebook', 'google', 'twitter', 'persona', 'liveconnect'),
                         get_available_providers())

    def test_get_providers(self):
        self.assertEqual([], get_providers({}, ''))
        self.assertEqual([{'name': 'facebook', 'is_current': True}],
                         get_providers({'facebook_id': 1234}, 'facebook'))
        self.assertEqual([{
                    'name': 'facebook',
                    'is_current': True,
                    }, {
                    'name': 'google',
                    'is_current': False,
                    }, {
                    'name': 'twitter',
                    'is_current': False,
                    }],
                          get_providers({'facebook_id': 1234,
                                         'google_id': 4321,
                                         'twitter_id': 6789}, 'facebook'))
        self.assertEqual([], get_providers({'myspace_id': 1234}, ''))

    def test_n_passwords(self):
        self.assertEqual(0, get_n_passwords(self.db, {'_id': 1}))

        self.db.passwords.insert({'password': 'secret', 'owner': 1})
        self.assertEqual(1, get_n_passwords(self.db, {'_id': 1}))

        self.db.passwords.insert({'password2': 'secret2', 'owner': 1})
        self.assertEqual(2, get_n_passwords(self.db, {'_id': 1}))
        self.db.passwords.insert({'password2': 'secret2', 'owner': 2})
        self.assertEqual(2, get_n_passwords(self.db, {'_id': 1}))

    def test_get_accounts_empty_user(self):
        self.assertEqual([], get_accounts(self.db, {}, ''))

    def test_get_accounts_empty_provider(self):
        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, ''))

    def test_get_accounts_one_user_no_provider(self):
        user_id = self.db.users.insert({'email': 'john@example.com'})
        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }, {
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': str(user_id),
            'is_verified': False,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, ''))

    def test_get_accounts_one_user_with_provider(self):
        user_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
        })
        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }, {
            'providers': [{
                'name': 'twitter',
                'is_current': False,
            }],
            'is_current': False,
            'passwords': 0,
            'id': str(user_id),
            'is_verified': False,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, ''))

    def test_get_accounts_one_user_with_provider_email_verified(self):
        user_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
            'email_verified': True,
        })
        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }, {
            'providers': [{
                'name': 'twitter',
                'is_current': True,
            }],
            'passwords': 0,
            'id': str(user_id),
            'is_current': True,
            'is_verified': True,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, 'twitter'))

    def test_get_accounts_user_with_passwords(self):
        user_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
            'email_verified': True,
        })
        self.db.passwords.insert({'password': 'secret', 'owner': user_id})
        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }, {
            'providers': [{
                'name': 'twitter',
                'is_current': False,
            }],
            'passwords': 1,
            'id': str(user_id),
            'is_current': False,
            'is_verified': True,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, 'google'))

    def test_get_accounts_user_multiple_providers(self):
        user_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
            'google_id': 4321,
            'email_verified': True,
        })
        self.db.passwords.insert({'password': 'secret', 'owner': user_id})

        self.assertEqual([{
            'providers': [],
            'is_current': False,
            'passwords': 0,
            'id': '',
            'is_verified': False,
        }, {
            'providers': [{
                'name': 'google',
                'is_current': True,
            }, {
                'name': 'twitter',
                'is_current': False,
            }],
            'passwords': 1,
            'id': str(user_id),
            'is_current': True,
            'is_verified': True,
        }], get_accounts(self.db, {
            'email': 'john@example.com',
            '_id': '',
        }, 'google'))


class BaseMergeTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        mdb = MongoDB(MONGO_URI)
        self.db = mdb.get_database()

    def tearDown(self):
        testing.tearDown()
        self.db.drop_collection('users')
        self.db.drop_collection('passwords')
        self.db.drop_collection('authorized_apps')

    def _add_authorized_app(self, user_id, client_id):
        self.db.authorized_apps.insert({
            'client_id': client_id,
            'user': user_id,
            'redirect_uri': 'http://example.com/callback',
            'response_type': 'code',
            'scope': 'scope1',
        })


class MergeAccountsTests(BaseMergeTests):

    def test_merge_empty_user(self):
        self.assertEqual(0, merge_accounts(self.db, {}, []))

    def _create_master_user(self):
        master_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
        })
        self._add_authorized_app(master_id, 'a')
        self._add_authorized_app(master_id, 'b')
        master_user = self.db.users.find_one({'_id': master_id})

        self.db.passwords.insert({
            'owner': master_id,
            'password1': 'secret1',
        })
        return master_id, master_user

    def test_merge_with_itself(self):
        master_id, master_user = self._create_master_user()

        self.assertEqual(1, self.db.users.count())
        self.assertEqual(0, merge_accounts(self.db, master_user,
                                           [str(master_id)]))
        master_user_reloaded = self.db.users.find_one({'_id': master_id})

        self.assertEqual(master_user, master_user_reloaded)
        self.assertEqual(1, self.db.users.count())

    def test_merge_with_invented_users(self):
        master_id, master_user = self._create_master_user()

        self.assertEqual(0, merge_accounts(self.db, master_user,
                                           ['000000000000000000000000']))
        master_user_reloaded = self.db.users.find_one({'_id': master_id})
        self.assertEqual(master_user, master_user_reloaded)
        self.assertEqual(1, self.db.users.count())

    def test_merge_valid_users(self):
        master_id, master_user = self._create_master_user()

        # let's create valid users
        other_id = self.db.users.insert({
            'email': 'john@example.com',
            'google_id': 4321,
        })
        self._add_authorized_app(other_id, 'b')
        self._add_authorized_app(other_id, 'c')
        self.assertEqual(2, self.db.users.count())
        self.db.passwords.insert({
            'owner': other_id,
            'password2': 'secret2',
        })

        self.assertEqual(1, merge_accounts(self.db, master_user,
                                           [str(other_id)]))
        master_user_reloaded = self.db.users.find_one({'_id': master_id})
        self.assertEqual({
            '_id': master_id,
            'email': 'john@example.com',
            'twitter_id': 1234,
            'google_id': 4321,
        }, master_user_reloaded)
        self.assertEqual(1, self.db.users.count())
        self.assertEqual(2,
                         self.db.passwords.find({'owner': master_id}).count())


class MergeUsersTests(BaseMergeTests):

    def test_merge_users(self):
        user1_id = self.db.users.insert({
            'email': 'john@example.com',
            'twitter_id': 1234,
        })
        self._add_authorized_app(user1_id, 'a')
        self._add_authorized_app(user1_id, 'b')
        self.db.passwords.insert({
            'owner': user1_id,
            'password': 'secret1',
        })
        self.db.passwords.insert({
            'owner': user1_id,
            'password': 'secret2',
        })
        user1 = self.db.users.find_one({'_id': user1_id})

        user2_id = self.db.users.insert({
            'email': 'john@example.com',
            'google_id': 4321,
        })
        self._add_authorized_app(user2_id, 'b')
        self._add_authorized_app(user2_id, 'c')
        self.db.passwords.insert({
            'owner': user2_id,
            'password': 'secret3',
        })
        self.db.passwords.insert({
            'owner': user2_id,
            'password': 'secret4',
        })
        user2 = self.db.users.find_one({'_id': user2_id})

        merge_users(self.db, user1, user2)
        self.assertEqual(4, self.db.passwords.find(
            {'owner': user1_id}).count())
        self.assertEqual(0, self.db.passwords.find(
            {'owner': user2_id}).count())
        self.assertEqual(None, self.db.users.find_one({'_id': user2_id}))
        user1_refreshed = self.db.users.find_one({'_id': user1_id})
        self.assertEqual(user1_refreshed, {
            '_id': user1_id,
            'email': 'john@example.com',
            'twitter_id': 1234,
            'google_id': 4321,
        })
        auths = self.db.authorized_apps.find({'user': user1_id})
        for real, expected in zip(auths, ['a', 'b', 'c']):
            self.assertEqual(real['client_id'], expected)

        auths = self.db.authorized_apps.find({'user': user2_id})
        self.assertEqual(auths.count(), 0)


class AccountRemovalNotificationTests(unittest.TestCase):

    def setUp(self):
        self.admin_emails = ['admin1@example.com', 'admin2@example.com']
        self.config = testing.setUp(settings={
                'admin_emails': self.admin_emails,
                })
        self.config.include('pyramid_mailer.testing')
        self.config.include('pyramid_chameleon')
        self.config.add_route('home', '/')

    def tearDown(self):
        testing.tearDown()

    def test_notify_admins_of_account_removal(self):
        request = DummyRequest()
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 0)

        user = {'first_name': 'John', 'last_name': 'Doe',
                'email': 'john@example.com'}
        reason = 'I do not trust free services'
        notify_admins_of_account_removal(request, user, reason)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject,
                        'A user has destroyed his Yith Library account')
        self.assertEqual(mailer.outbox[0].recipients, self.admin_emails)
        self.assertTrue('John Doe <john@example.com' in mailer.outbox[0].body)
        self.assertTrue('I do not trust free services' in mailer.outbox[0].body)
