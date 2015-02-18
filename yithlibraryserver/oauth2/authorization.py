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

from oauthlib.oauth2 import Server

from pyramid.httpexceptions import HTTPUnauthorized

from yithlibraryserver.oauth2.utils import extract_params
from yithlibraryserver.oauth2.validator import RequestValidator


class Authorizator(object):

    def __init__(self, db):
        self.db = db

    def _get_record(self, scopes, credentials):
        return {
            'client_id': credentials['client_id'],
            'user': credentials['user']['_id'],
            'redirect_uri': credentials['redirect_uri'],
            'response_type': credentials['response_type'],
            'scope': ' '.join(scopes),
        }

    def is_app_authorized(self, scopes, credentials):
        record = self._get_record(scopes, credentials)
        return self.db.authorized_apps.find_one(record) is not None

    def store_user_authorization(self, scopes, credentials):
        record = self._get_record(scopes, credentials)
        self.db.authorized_apps.remove(record)
        self.db.authorized_apps.insert(record)

    def get_user_authorizations(self, user):
        return self.db.authorized_apps.find({'user': user['_id']})

    def remove_user_authorization(self, user, client_id):
        self.db.authorized_apps.remove({
            'client_id': client_id,
            'user': user['_id'],
        })

    def remove_all_user_authorizations(self, user):
        self.db.authorized_apps.remove({
            'user': user['_id'],
        })


def verify_request(request, scopes):
    validator = RequestValidator(request.db)
    server = Server(validator)

    uri, http_method, body, headers = extract_params(request)

    valid, r = server.verify_request(
        uri, http_method, body, headers, scopes,
    )

    if not valid:
        raise HTTPUnauthorized()

    user = request.db.users.find_one(r.user)
    if user is None:
        raise HTTPUnauthorized()

    return user
