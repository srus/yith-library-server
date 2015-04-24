# Yith Library Server is a password storage server.
# Copyright (C) 2013-2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

import gzip

from freezegun import freeze_time

from pyramid_sqlalchemy import Session

import transaction

from yithlibraryserver.compat import text_type, BytesIO
from yithlibraryserver.password.models import Password
from yithlibraryserver.testing import TestCase
from yithlibraryserver.user.models import User
from yithlibraryserver.user.tests.test_views import create_and_login_user


def get_gzip_data(text):
    buf = BytesIO()
    gzip_data = gzip.GzipFile(fileobj=buf, mode='wb')
    gzip_data.write(text.encode('utf-8'))
    gzip_data.close()
    return buf.getvalue()


class ViewTests(TestCase):

    def assertUncompressData(self, body, data):
        buf = BytesIO(body)
        gzip_file = gzip.GzipFile(fileobj=buf, mode='rb')
        self.assertEqual(gzip_file.read().decode('utf-8'), data)

    def test_backups_index_requires_authentication(self):
        res = self.testapp.get('/backup')
        self.assertEqual(res.status, '200 OK')
        res.mustcontain('Log in')

    def test_backups_index(self):
        create_and_login_user(self.testapp)
        res = self.testapp.get('/backup')
        self.assertEqual(res.status, '200 OK')
        res.mustcontain('Backup', 'Export passwords', 'Import passwords')

    def test_backups_export_requires_authentication(self):
        res = self.testapp.get('/backup/export')
        self.assertEqual(res.status, '200 OK')
        res.mustcontain('Log in')

    def test_backups_export_empty_passwords(self):
        create_and_login_user(self.testapp)

        with freeze_time('2012-01-10'):
            res = self.testapp.get('/backup/export')
            self.assertEqual(res.status, '200 OK')
            self.assertEqual(res.content_type, 'application/yith-library')
            self.assertUncompressData(res.body, '[]')
            self.assertEqual(
                res.content_disposition,
                'attachment; filename=yith-library-backup-2012-01-10.yith',
            )

    def test_backups_export_some_passwords(self):
        user_id = create_and_login_user(self.testapp)

        with freeze_time('2012-12-12 12:12:12'):
            password1 = Password(secret='secret1', user_id=user_id)
            password2 = Password(secret='secret2', user_id=user_id)

            with transaction.manager:
                Session.add(password1)
                Session.add(password2)
                Session.flush()

        with freeze_time('2012-01-10'):
            res = self.testapp.get('/backup/export')
            self.assertEqual(res.status, '200 OK')
            self.assertEqual(res.content_type, 'application/yith-library')
            self.assertUncompressData(
                res.body,
                '[{"account": "", "service": "", "tags": [], "notes": "", "creation": "2012-12-12T12:12:12", "secret": "secret1", "expiration": null, "modification": "2012-12-12T12:12:12"}, '
                '{"account": "", "service": "", "tags": [], "notes": "", "creation": "2012-12-12T12:12:12", "secret": "secret2", "expiration": null, "modification": "2012-12-12T12:12:12"}]',
            )
            self.assertEqual(
                res.content_disposition,
                'attachment; filename=yith-library-backup-2012-01-10.yith',
            )

    def test_backups_import_requires_authentication(self):
        res = self.testapp.post('/backup/import')
        self.assertEqual(res.status, '200 OK')
        res.mustcontain('Log in')

    def test_backups_import_no_file_to_upload(self):
        create_and_login_user(self.testapp)

        res = self.testapp.post('/backup/import', status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')

        self.assertEqual(0, Session.query(Password).count())

    def test_backups_import_not_a_file(self):
        create_and_login_user(self.testapp)

        res = self.testapp.post('/backup/import', {
            'passwords-file': '',
        }, status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')

        self.assertEqual(0, Session.query(Password).count())

    def test_backups_import_bad_file(self):
        create_and_login_user(self.testapp)

        content = get_gzip_data(text_type('[{}'))
        res = self.testapp.post(
            '/backup/import', {},
            upload_files=[('passwords-file', 'bad.json', content)],
            status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')

        self.assertEqual(0, Session.query(Password).count())

    def test_backups_import_empty_file(self):
        create_and_login_user(self.testapp)

        content = get_gzip_data(text_type('[]'))
        res = self.testapp.post(
            '/backup/import', {},
            upload_files=[('passwords-file', 'empty.json', content)],
            status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')

        self.assertEqual(0, Session.query(Password).count())

    def test_backups_import_empty_file2(self):
        create_and_login_user(self.testapp)

        content = get_gzip_data(text_type('[{}]'))
        res = self.testapp.post(
            '/backup/import', {},
            upload_files=[('passwords-file', 'empty.json', content)],
            status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')

        self.assertEqual(0, Session.query(Password).count())

    def test_backups_import_good_file(self):
        user_id = create_and_login_user(self.testapp)
        content = get_gzip_data(text_type('[{"secret": "password1"}, {"secret": "password2"}]'))
        res = self.testapp.post(
            '/backup/import', {},
            upload_files=[('passwords-file', 'good.json', content)],
            status=302)
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/backup')
        self.assertEqual(2, Session.query(Password).count())
        user = Session.query(User).filter(User.id==user_id).one()
        self.assertEqual(len(user.passwords), 2)
