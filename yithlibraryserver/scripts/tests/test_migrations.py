# Yith Library Server is a password storage server.
# Copyright (C) 2013-2014 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

import sys

from yithlibraryserver.compat import StringIO
from yithlibraryserver.oauth2.authorization import Authorizator
from yithlibraryserver.scripts.migrations import migrate
from yithlibraryserver.scripts.testing import ScriptTests


class BaseMigrationsTests(ScriptTests):

    def setUp(self):
        super(BaseMigrationsTests, self).setUp()
        self.old_args = sys.argv[:]
        self.old_stdout = sys.stdout

    def tearDown(self):
        super(BaseMigrationsTests, self).tearDown()
        # Restore sys.values
        sys.argv = self.old_args
        sys.stdout = self.old_stdout


class MigrationsTests(BaseMigrationsTests):

    def test_no_arguments(self):
        sys.argv = []
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide two arguments. The first one is the config file and the second one is the migration name.\n')

    def test_no_migration_name(self):
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide two arguments. The first one is the config file and the second one is the migration name.\n')

    def test_bad_migration_name(self):
        sys.argv = ['notused', self.conf_file_path, 'bad_migration']
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, 3)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'The migration "bad_migration" does not exist.\n')


class AddSendEmailPreferenceTests(BaseMigrationsTests):

    clean_collections = ('users', )

    def test_no_users(self):
        sys.argv = ['notused', self.conf_file_path, 'add_send_email_preference']
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

    def test_some_users(self):
        # Add some users
        u1_id = self.db.users.insert({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
        })
        self.db.users.insert({
            'first_name': 'John2',
            'last_name': 'Doe2',
            'email': 'john2@example.com',
            'send_passwords_periodically': False,
        })
        sys.argv = ['notused', self.conf_file_path, 'add_send_email_preference']
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        expected_output = """Adding attribute "send_passwords_periodically" to John Doe <john@example.com>
"""
        self.assertEqual(stdout, expected_output)

        user1 = self.db.users.find_one({'_id': u1_id})
        self.assertEqual(user1['send_passwords_periodically'], True)


class NewAuthorizedAppsCollectionTests(BaseMigrationsTests):

    clean_collections = ('users', 'applications', 'authorized_apps')

    def test_no_users(self):
        sys.argv = ['notused', self.conf_file_path, 'new_authorized_apps_collection']
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

    def test_some_users(self):
        authorizator = Authorizator(self.db)

        app1_id = self.db.applications.insert({
            'client_id': 'app1',
            'callback_url': 'https://example.com/callback/1',
        })
        app2_id = self.db.applications.insert({
            'client_id': 'app2',
            'callback_url': 'https://example.com/callback/2',
        })

        u1_id = self.db.users.insert({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'authorized_apps': [app1_id, app2_id],
        })
        auths = authorizator.get_user_authorizations({'_id': u1_id})
        self.assertEqual(auths.count(), 0)
        u2_id = self.db.users.insert({
            'first_name': 'John2',
            'last_name': 'Doe2',
            'email': 'john2@example.com',
            'send_passwords_periodically': False,
            'authorized_apps': [app1_id],
        })
        auths = authorizator.get_user_authorizations({'_id': u2_id})
        self.assertEqual(auths.count(), 0)

        sys.argv = ['notused', self.conf_file_path, 'new_authorized_apps_collection']
        sys.stdout = StringIO()
        result = migrate()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        stdout = sys.stdout.getvalue()
        expected_output = """Storing authorized app "app1" for user John Doe <john@example.com>
Storing authorized app "app2" for user John Doe <john@example.com>
Storing authorized app "app1" for user John2 Doe2 <john2@example.com>
"""
        self.assertEqual(stdout, expected_output)

        user1 = self.db.users.find_one({'_id': u1_id})
        self.assertNotIn('authorized_apps', user1)
        auths = authorizator.get_user_authorizations({'_id': u1_id})
        self.assertEqual(auths.count(), 2)

        user2 = self.db.users.find_one({'_id': u2_id})
        self.assertNotIn('authorized_apps', user2)
        auths = authorizator.get_user_authorizations({'_id': u2_id})
        self.assertEqual(auths.count(), 1)

