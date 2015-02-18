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

import datetime
import sys

import bson
from freezegun import freeze_time

from yithlibraryserver.backups.email import get_day_to_send
from yithlibraryserver.compat import StringIO
from yithlibraryserver.scripts.backups import send_backups_via_email
from yithlibraryserver.scripts.testing import ScriptTests


class BackupsTests(ScriptTests):

    def setUp(self):
        super(BackupsTests, self).setUp()

        # Save sys values
        self.old_args = sys.argv[:]
        self.old_stdout = sys.stdout

        self.freezer = freeze_time('2012-01-26')
        self.freezer.start()

    def tearDown(self):
        # Restore sys.values
        sys.argv = self.old_args
        sys.stdout = self.old_stdout

        self.freezer.stop()

        super(BackupsTests, self).tearDown()

    def test_no_arguments(self):
        # Replace sys argv and stdout
        sys.argv = []
        sys.stdout = StringIO()

        # Call send backups with no arguments
        result = send_backups_via_email()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide at least one argument\n')

    def test_empty_database(self):
        # Call send backups with a config file but an empty database
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = send_backups_via_email()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

    def test_send_specific_user(self):
        self.add_passwords(self.db.users.insert({
            'first_name': 'John1',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'send_passwords_periodically': False,
        }), 10)
        self.add_passwords(self.db.users.insert({
            'first_name': 'John2',
            'last_name': 'Doe',
            'email': 'john2@example.com',
            'email_verified': True,
            'send_passwords_periodically': False,
        }), 10)
        self.add_passwords(self.db.users.insert({
            'first_name': 'John3',
            'last_name': 'Doe',
            'email': 'john3@example.com',
            'email_verified': True,
            'send_passwords_periodically': True,
        }), 10)
        self.add_passwords(self.db.users.insert({
            'first_name': 'John4',
            'last_name': 'Doe',
            'email': 'john4@example.com',
            'email_verified': True,
            'send_passwords_periodically': True,
        }), 10)

        sys.argv = ['notused', self.conf_file_path, 'john3@example.com']
        sys.stdout = StringIO()
        result = send_backups_via_email()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        expected_output = """Passwords sent to John3 Doe <john3@example.com>
"""
        self.assertEqual(stdout, expected_output)

    def test_several_users(self):
        date_joined = datetime.datetime(2012, 12, 12, 12, 12)
        # Add some users
        self.add_passwords(self.db.users.insert({
            'first_name': 'John1',
            'last_name': 'Doe',
            'date_joined': date_joined,
            'email': 'john1@example.com',
            'email_verified': False,
            'send_passwords_periodically': False,
        }), 10)

        user2_id = self.add_passwords(self.db.users.insert({
            '_id': bson.objectid.ObjectId('100000000000000000000000'),
            'first_name': 'John2',
            'last_name': 'Doe',
            'date_joined': date_joined,
            'email': 'john2@example.com',
            'email_verified': True,
            'send_passwords_periodically': True,
        }), 10)
        day = get_day_to_send({'_id': user2_id}, 28)
        self.assertEqual(day, 6)

        user3_id = self.add_passwords(self.db.users.insert({
            '_id': bson.objectid.ObjectId('00000000000000000000000a'),
            'first_name': 'John3',
            'last_name': 'Doe',
            'date_joined': date_joined,
            'email': 'john3@example.com',
            'email_verified': True,
            'send_passwords_periodically': True,
        }), 10)
        day = get_day_to_send({'_id': user3_id}, 28)
        self.assertEqual(day, 26)

        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = send_backups_via_email()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        expected_output = """Passwords sent to John3 Doe <john3@example.com>
"""
        self.assertEqual(stdout, expected_output)
