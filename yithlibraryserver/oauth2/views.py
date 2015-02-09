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

import bson
from deform import Button, Form, ValidationFailure

from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPFound,
    HTTPNotFound,
)
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config

from oauthlib.oauth2 import (
    AccessDeniedError,
    FatalClientError,
    OAuth2Error,
    Server,
)

from yithlibraryserver.i18n import TranslationString as _
from yithlibraryserver.oauth2.application import create_client_id_and_secret
from yithlibraryserver.oauth2.authorization import Authorizator
from yithlibraryserver.oauth2.schemas import ApplicationSchema
from yithlibraryserver.oauth2.schemas import FullApplicationSchema
from yithlibraryserver.oauth2.utils import (
    create_response,
    extract_params,
    response_from_error,
)
from yithlibraryserver.oauth2.validator import RequestValidator
from yithlibraryserver.schemas import HorizontalForm
from yithlibraryserver.user.security import assert_authenticated_user_is_registered


@view_config(route_name='oauth2_developer_applications',
             renderer='templates/developer_applications.pt',
             permission='view-applications')
def developer_applications(request):
    assert_authenticated_user_is_registered(request)
    owned_apps_filter = {'owner': request.user['_id']}
    return {
        'applications': request.db.applications.find(owned_apps_filter)
        }


@view_config(route_name='oauth2_developer_application_new',
             renderer='templates/developer_application_new.pt',
             permission='add-application')
def developer_application_new(request):
    assert_authenticated_user_is_registered(request)
    schema = ApplicationSchema()
    button1 = Button('submit', _('Save application'))
    button1.css_class = 'btn-primary'
    button2 = Button('cancel', _('Cancel'))
    button2.css_class = ''
    form = HorizontalForm(schema, buttons=(button1, button2))

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'form': e.render()}

        # the data is fine, save into the db
        application = {
            'owner': request.user['_id'],
            'name': appstruct['name'],
            'main_url': appstruct['main_url'],
            'callback_url': appstruct['callback_url'],
            'authorized_origins': appstruct['authorized_origins'],
            'production_ready': appstruct['production_ready'],
            'image_url': appstruct['image_url'],
            'description': appstruct['description'],
            }
        create_client_id_and_secret(application)

        request.session.flash(
            _('The application ${app} was created successfully',
              mapping={'app': appstruct['name']}),
            'success')

        request.db.applications.insert(application)
        return HTTPFound(
            location=request.route_path('oauth2_developer_applications'))
    elif 'cancel' in request.POST:
        return HTTPFound(
            location=request.route_path('oauth2_developer_applications'))

    # this is a GET
    return {'form': form.render()}


@view_config(route_name='oauth2_developer_application_edit',
             renderer='templates/developer_application_edit.pt',
             permission='edit-application')
def developer_application_edit(request):
    try:
        app_id = bson.ObjectId(request.matchdict['app'])
    except bson.errors.InvalidId:
        return HTTPBadRequest(body='Invalid application id')

    assert_authenticated_user_is_registered(request)

    app = request.db.applications.find_one(app_id)
    if app is None:
        return HTTPNotFound()

    if app['owner'] != request.user['_id']:
        return HTTPUnauthorized()

    schema = FullApplicationSchema()
    button1 = Button('submit', _('Save application'))
    button1.css_class = 'btn-primary'
    button2 = Button('delete', _('Delete application'))
    button2.css_class = 'btn-danger'
    button3 = Button('cancel', _('Cancel'))
    button3.css_class = ''
    form = HorizontalForm(schema, buttons=(button1, button2, button3))

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'form': e.render(), 'app': app}

        # the data is fine, save into the db
        application = {
            'owner': request.user['_id'],
            'name': appstruct['name'],
            'main_url': appstruct['main_url'],
            'callback_url': appstruct['callback_url'],
            'authorized_origins': appstruct['authorized_origins'],
            'production_ready': appstruct['production_ready'],
            'image_url': appstruct['image_url'],
            'description': appstruct['description'],
            'client_id': app['client_id'],
            'client_secret': app['client_secret'],
            }

        request.db.applications.update({'_id': app['_id']},
                                       application)

        request.session.flash(_('The changes were saved successfully'),
                              'success')

        return HTTPFound(
            location=request.route_path('oauth2_developer_applications'))
    elif 'delete' in request.POST:
        return HTTPFound(
            location=request.route_path('oauth2_developer_application_delete',
                                        app=app['_id']))
    elif 'cancel' in request.POST:
        return HTTPFound(
            location=request.route_path('oauth2_developer_applications'))

    # this is a GET
    return {'form': form.render(app), 'app': app}


@view_config(route_name='oauth2_developer_application_delete',
             renderer='templates/developer_application_delete.pt',
             permission='delete-application')
def developer_application_delete(request):
    try:
        app_id = bson.ObjectId(request.matchdict['app'])
    except bson.errors.InvalidId:
        return HTTPBadRequest(body='Invalid application id')

    app = request.db.applications.find_one(app_id)
    if app is None:
        return HTTPNotFound()

    assert_authenticated_user_is_registered(request)
    if app['owner'] != request.user['_id']:
        return HTTPUnauthorized()

    if 'submit' in request.POST:
        request.db.applications.remove(app_id)
        request.session.flash(
            _('The application ${app} was deleted successfully',
              mapping={'app': app['name']}),
            'success',
            )
        return HTTPFound(
            location=request.route_path('oauth2_developer_applications'))

    return {'app': app}


class AuthorizationEndpoint(object):

    def __init__(self, request):
        self.request = request
        self.validator = RequestValidator(request.db, request.datetime_service)
        self.server = Server(self.validator)
        self.authorizator = Authorizator(request.db)

    @view_config(route_name='oauth2_authorization_endpoint',
                 renderer='templates/application_authorization.pt',
                 permission='add-authorized-app',
                 request_method='GET')
    def get(self):
        uri, http_method, body, headers = extract_params(self.request)

        try:
            scopes, credentials = self.server.validate_authorization_request(
                uri, http_method, body, headers,
            )
            credentials['user'] = self.request.user

            if self.authorizator.is_app_authorized(scopes, credentials):
                server_response = self.server.create_authorization_response(
                    uri, http_method, body, headers, scopes, credentials,
                )
                return create_response(*server_response)
            else:
                app = self.validator.get_client(credentials['client_id'])
                authorship_information = ''
                owner_id = app._client.get('owner', None)
                if owner_id is not None:
                    owner = self.request.db.users.find_one({'_id': owner_id})
                    if owner:
                        email = owner.get('email', None)
                        if email:
                            authorship_information = email

                pretty_scopes = self.validator.get_pretty_scopes(scopes)
                return {
                    'response_type': credentials['response_type'],
                    'client_id': credentials['client_id'],
                    'redirect_uri': credentials['redirect_uri'],
                    'state': credentials['state'],
                    'scope': ' '.join(scopes),
                    'app': app._client,
                    'scopes': pretty_scopes,
                    'authorship_information': authorship_information,
                }
        except FatalClientError as e:
            return response_from_error(e)

        except OAuth2Error as e:
            return HTTPFound(e.in_uri(e.redirect_uri))

    @view_config(route_name='oauth2_authorization_endpoint',
                 permission='add-authorized-app',
                 request_method='POST')
    def post(self):
        uri, http_method, body, headers = extract_params(self.request)

        redirect_uri = self.request.POST.get('redirect_uri')
        if 'submit' in self.request.POST:
            scope = self.request.POST.get('scope', '')
            scopes = scope.split()
            credentials = {
                'client_id': self.request.POST.get('client_id'),
                'redirect_uri': redirect_uri,
                'response_type': self.request.POST.get('response_type'),
                'state': self.request.POST.get('state'),
                'user': self.request.user,
            }
            try:
                server_response = self.server.create_authorization_response(
                    uri, http_method, body, headers, scopes, credentials,
                )
                self.authorizator.store_user_authorization(scopes, credentials)
                return create_response(*server_response)
            except FatalClientError as e:
                return response_from_error(e)

        elif 'cancel' in self.request.POST:
            e = AccessDeniedError()
            return HTTPFound(e.in_uri(redirect_uri))


@view_config(route_name='oauth2_token_endpoint',
             renderer='json')
def token_endpoint(request):
    validator = RequestValidator(request.db, request.datetime_service)
    server = Server(validator)

    uri, http_method, body, headers = extract_params(request)
    server_response = server.create_token_response(
        uri, http_method, body, headers, {},
    )
    return create_response(*server_response)


@view_config(route_name='oauth2_authorized_applications',
             renderer='templates/authorized_applications.pt',
             permission='view-applications')
def authorized_applications(request):
    assert_authenticated_user_is_registered(request)
    authorizator = Authorizator(request.db)
    authorized_apps = []
    for authorization in authorizator.get_user_authorizations(request.user):
        app = request.db.applications.find_one({
            'client_id': authorization['client_id'],
        })
        if app is not None:
            authorized_apps.append(app)
    return {'authorized_apps': authorized_apps}


@view_config(route_name='oauth2_revoke_application',
             renderer='templates/application_revoke_authorization.pt',
             permission='revoke-authorized-app')
def revoke_application(request):
    assert_authenticated_user_is_registered(request)

    try:
        app_id = bson.ObjectId(request.matchdict['app'])
    except bson.errors.InvalidId:
        return HTTPBadRequest(body='Invalid application id')

    app = request.db.applications.find_one(app_id)
    if app is None:
        return HTTPNotFound()

    authorizator = Authorizator(request.db)

    if 'submit' in request.POST:
        authorizator.remove_user_authorization(request.user, app['client_id'])

        request.session.flash(
            _('The access to application ${app} has been revoked',
              mapping={'app': app['name']}),
            'success',
            )
        return HTTPFound(
            location=request.route_path('oauth2_authorized_applications'))

    return {'app': app}


@view_config(route_name='oauth2_clients',
             renderer='templates/clients.pt')
def clients(request):
    return {'apps': request.db.applications.find({'production_ready': True})}
