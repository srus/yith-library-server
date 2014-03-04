# Yith Library Server is a password storage server.
# Copyright (C) 2012-2013 Yaco Sistemas
# Copyright (C) 2012-2013 Alejandro Blanco Escudero <alejandro.b.e@gmail.com>
# Copyright (C) 2012-2013 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

import json

import bson

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config, view_defaults

from yithlibraryserver.errors import password_not_found, invalid_password_id
from yithlibraryserver.oauth2.decorators import protected_method
from yithlibraryserver.password.models import PasswordsManager
from yithlibraryserver.password.validation import validate_password


@view_defaults(route_name='password_collection_view', renderer='json')
class PasswordCollectionRESTView(object):

    def __init__(self, request):
        self.request = request
        self.passwords_manager = PasswordsManager(request.db)

    @view_config(request_method='OPTIONS', renderer='string')
    def options(self):
        headers = self.request.response.headers
        headers['Access-Control-Allow-Methods'] = 'GET, POST'
        headers['Access-Control-Allow-Headers'] = ('Origin, Content-Type, '
                                                   'Accept, Authorization')
        return ''

    @view_config(request_method='GET')
    @protected_method(['read-passwords'])
    def get(self):
        passwords = list(self.passwords_manager.retrieve(self.request.user))
        for p in passwords:
            p['id'] = p['_id']
        return {"passwords": passwords}

    @view_config(request_method='POST')
    @protected_method(['write-passwords'])
    def post(self):
        password, errors = validate_password(self.request.body,
                                             self.request.charset)

        if errors:
            result = {'message': ','.join(errors)}
            return HTTPBadRequest(body=json.dumps(result),
                                  content_type='application/json')

        result = self.passwords_manager.create(self.request.user, password)
        result['id'] = result['_id']
        return {'password': result}


@view_defaults(route_name='password_view', renderer='json')
class PasswordRESTView(object):

    def __init__(self, request):
        self.request = request
        self.passwords_manager = PasswordsManager(request.db)
        self.password_id = self.request.matchdict['password']

    @view_config(request_method='OPTIONS', renderer='string')
    def options(self):
        headers = self.request.response.headers
        headers['Access-Control-Allow-Methods'] = 'GET, PUT, DELETE'
        headers['Access-Control-Allow-Headers'] = ('Origin, Content-Type, '
                                                   'Accept, Authorization')
        return ''

    @view_config(request_method='GET')
    @protected_method(['read-passwords'])
    def get(self):
        try:
            _id = bson.ObjectId(self.password_id)
        except bson.errors.InvalidId:
            return invalid_password_id()

        password = self.passwords_manager.retrieve(self.request.user, _id)

        if password is None:
            return password_not_found()
        else:
            password['id'] = password['_id']
            return {'password': password}

    @view_config(request_method='PUT')
    @protected_method(['write-passwords'])
    def put(self):
        try:
            _id = bson.ObjectId(self.password_id)
        except bson.errors.InvalidId:
            return invalid_password_id()

        password, errors = validate_password(self.request.body,
                                             self.request.charset,
                                             _id)

        if errors:
            result = {'message': ','.join(errors)}
            return HTTPBadRequest(body=json.dumps(result),
                                  content_type='application/json')

        result = self.passwords_manager.update(self.request.user, _id,
                                               password)
        if result is None:
            return password_not_found()
        else:
            result['id'] = result['_id']
            return {'password': result}

    @view_config(request_method='DELETE')
    @protected_method(['write-passwords'])
    def delete(self):
        try:
            _id = bson.ObjectId(self.password_id)
        except bson.errors.InvalidId:
            return invalid_password_id()

        if self.passwords_manager.delete(self.request.user, _id):
            return {'password': {'id': _id}}
        else:
            return password_not_found()
