# Yith Library Server is a password storage server.
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
import sys

from yithlibraryserver.compat import StringIO
from yithlibraryserver.scripts.reports import users, applications, statistics
from yithlibraryserver.scripts.testing import ScriptTests


class ReportTests(ScriptTests):

    def test_users(self):
        # Save sys values
        old_args = sys.argv[:]
        old_stdout = sys.stdout

        # Replace sys argv and stdout
        sys.argv = []
        sys.stdout = StringIO()

        # Call users with no arguments
        result = users()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide at least one argument\n')

        # Call users with a config file but an empty database
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = users()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

        # Add some data to the database
        u1_id = self.db.users.insert({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
        })
        u2_id = self.db.users.insert({
            'first_name': 'John2',
            'last_name': 'Doe2',
            'email': 'john2@example.com',
            'email_verified': True,
            'twitter_id': '1234',
        })
        self.db.passwords.insert({
            'service': 'service1',
            'secret': 's3cr3t',
            'owner': u2_id,
        })
        u3_id = self.db.users.insert({
            'first_name': 'John3',
            'last_name': 'Doe3',
            'email': 'john3@example.com',
            'email_verified': True,
            'twitter_id': '1234',
            'facebook_id': '5678',
            'google_id': 'abcd',
            'date_joined': datetime.datetime(2012, 12, 12, 12, 12, 12),
            'last_login': datetime.datetime(2012, 12, 12, 12, 12, 12),
        })
        self.db.passwords.insert({
            'service': 'service1',
            'secret': 's3cr3t',
            'owner': u3_id,
        })
        self.db.passwords.insert({
            'service': 'service2',
            'secret': 's3cr3t',
            'owner': u3_id,
        })
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = users()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        context = {
            'u1': u1_id,
            'u2': u2_id,
            'u3': u3_id,
            'tab': '\t',
        }
        expected_output = """John Doe <john@example.com> (%(u1)s)
%(tab)sPasswords: 0
%(tab)sProviders:
%(tab)sVerified: False
%(tab)sDate joined: Unknown
%(tab)sLast login: Unknown

John2 Doe2 <john2@example.com> (%(u2)s)
%(tab)sPasswords: 1
%(tab)sProviders: twitter
%(tab)sVerified: True
%(tab)sDate joined: Unknown
%(tab)sLast login: Unknown

John3 Doe3 <john3@example.com> (%(u3)s)
%(tab)sPasswords: 2
%(tab)sProviders: facebook, google, twitter
%(tab)sVerified: True
%(tab)sDate joined: 2012-12-12 12:12:12+00:00
%(tab)sLast login: 2012-12-12 12:12:12+00:00

""" % context
        self.assertEqual(stdout, expected_output)

        # Restore sys.values
        sys.argv = old_args
        sys.stdout = old_stdout

    def test_applications(self):
        # Save sys values
        old_args = sys.argv[:]
        old_stdout = sys.stdout

        # Replace sys argv and stdout
        sys.argv = []
        sys.stdout = StringIO()

        # Call applications with no arguments
        result = applications()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide at least one argument\n')

        # Call applications with a config file but an empty database
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = applications()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

        # Add some data to the database
        u1_id = self.db.users.insert({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
        })
        self.db.applications.insert({
            'name': 'Test application 1',
            'owner': u1_id,
            'main_url': 'http://example.com/',
            'callback_url': 'http://example.com/callback',
            'client_id': '1234',
        })
        self.db.applications.insert({
            'name': 'Test application 2',
            'owner': '000000000000000000000000',
            'main_url': 'http://2.example.com/',
            'callback_url': 'http://2.example.com/callback',
            'client_id': '5678',
        })
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = applications()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        expected_output = """Test application 1
%(tab)sOwner: John Doe <john@example.com>
%(tab)sMain URL: http://example.com/
%(tab)sCallback URL: http://example.com/callback
%(tab)sUsers: 0

Test application 2
%(tab)sOwner: Unknown owner (000000000000000000000000)
%(tab)sMain URL: http://2.example.com/
%(tab)sCallback URL: http://2.example.com/callback
%(tab)sUsers: 0

""" % {'tab': '\t'}
        self.assertEqual(stdout, expected_output)

        # Restore sys.values
        sys.argv = old_args
        sys.stdout = old_stdout

    def test_statistics(self):
        # Save sys values
        old_args = sys.argv[:]
        old_stdout = sys.stdout

        # Replace sys argv and stdout
        sys.argv = []
        sys.stdout = StringIO()

        # Call statistics with no arguments
        result = statistics()
        self.assertEqual(result, 2)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, 'You must provide at least one argument\n')

        # Call statistics with a config file but an empty database
        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = statistics()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()
        self.assertEqual(stdout, '')

        # Add some data to the database
        u1_id = self.db.users.insert({
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'email_verified': True,
            'allow_google_analytics': True,
            'google_id': '1',
        })
        self.add_passwords(u1_id, 10)

        u2_id = self.db.users.insert({
            'first_name': 'Peter',
            'last_name': 'Doe',
            'email': 'peter@example.com',
            'email_verified': True,
            'allow_google_analytics': False,
            'twitter_id': '1',
        })
        self.add_passwords(u2_id, 20)

        u3_id = self.db.users.insert({
            'first_name': 'Susan',
            'last_name': 'Doe',
            'email': 'susan@example2.com',
            'email_verified': True,
            'allow_google_analytics': False,
            'facebook_id': '1',
        })
        self.add_passwords(u3_id, 15)

        self.db.users.insert({
            'first_name': 'Alice',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'persona_id': '1',
        })

        self.db.users.insert({
            'first_name': 'Bob',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'google_id': '2',
        })
        self.db.users.insert({
            'first_name': 'Kevin',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'google_id': '3',
        })
        self.db.users.insert({
            'first_name': 'Maria',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'google_id': '4',
        })
        self.db.users.insert({
            'first_name': 'Bran',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'twitter_id': '2',
        })
        self.db.users.insert({
            'first_name': 'George',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'twitter_id': '3',
        })
        self.db.users.insert({
            'first_name': 'Travis',
            'last_name': 'Doe',
            'email': '',
            'email_verified': False,
            'allow_google_analytics': False,
            'persona_id': '2',
        })

        sys.argv = ['notused', self.conf_file_path]
        sys.stdout = StringIO()
        result = statistics()
        self.assertEqual(result, None)
        stdout = sys.stdout.getvalue()

        expected_output = """Number of users: 10
Number of passwords: 45
Verified users: 30.00%% (3)
Users that allow Google Analytics cookie: 10.00%% (1)
Identity providers:
%(tab)sgoogle: 40.00%% (4)
%(tab)stwitter: 30.00%% (3)
%(tab)spersona: 20.00%% (2)
%(tab)sfacebook: 10.00%% (1)
Email providers:
%(tab)sexample.com: 66.67%% (2)
%(tab)sOthers: 33.33%% (1)
Users without email: 70.00%% (7)
Most active users:
%(tab)sPeter Doe <peter@example.com>: 20
%(tab)sSusan Doe <susan@example2.com>: 15
%(tab)sJohn Doe <john@example.com>: 10
Users without passwords: 70.00%% (7)
""" % {'tab': '\t'}
        self.assertEqual(stdout, expected_output)

        # Restore sys.values
        sys.argv = old_args
        sys.stdout = old_stdout
