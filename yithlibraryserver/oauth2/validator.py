# Yith Library Server is a password storage server.
# Copyright (C) 2014 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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
import logging

from bson.tz_util import utc

import oauthlib.oauth2
from oauthlib.common import to_unicode

from yithlibraryserver.i18n import TranslationString as _
from yithlibraryserver.oauth2.utils import decode_base64


logger = logging.getLogger(__name__)


class WrappedClient(object):

    def __init__(self, client):
        self._client = client
        for key, value in client.items():
            setattr(self, key, value)


class RequestValidator(oauthlib.oauth2.RequestValidator):

    scopes = {
        'read-passwords': _('Access your passwords'),
        'write-passwords': _('Modify your passwords'),
        'read-userinfo': _('Access your user information'),
    }

    def __init__(self, db, default_scopes=None):
        self.db = db
        if default_scopes is None:
            self.default_scopes = ['read-passwords']
        else:
            self.default_scopes = default_scopes

    def get_client(self, client_id):
        client = self.db.applications.find_one(
            {'client_id': client_id}
        )
        if client is not None:
            return WrappedClient(client)

    def get_pretty_scopes(self, scopes):
        return [self.scopes.get(scope) for scope in scopes]

    # Pre- and post-authorization

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Simple validity check, does client exist? Not banned?"""
        request.client = self.get_client(client_id)
        result = request.client is not None
        logger.debug('Validating client id: %s Result: %s', client_id, result)
        return result

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        """Is the client allowed to use the supplied redirect_uri?
        i.e. has the client previously registered this EXACT redirect uri.
        """
        client = request.client or self.get_client(client_id)
        return client.callback_url == redirect_uri

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """The redirect used if none has been supplied.

        Prefer your clients to pre register a redirect uri rather than
        supplying one on each authorization request.
        """
        client = request.client or self.get_client(client_id)
        return client.callback_url

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """Is the client allowed to access the requested scopes?"""
        valid_scopes = self.scopes.keys()
        return set(valid_scopes).issuperset(set(scopes))

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """Scopes a client will authorize for if none are supplied in the
        authorization request.
        """
        return self.default_scopes

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """Clients should only be allowed to use one type of response type, the
        one associated with their one allowed grant type.

        In this case it must be "code" or "token".
        """
        # TODO: store the allowed types in the client
        return response_type in ('code', 'token')

    # Post-authorization

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        """Remember to associate it with request.scopes, request.redirect_uri
        request.client, request.state and request.user

        (the last is passed in post_authorization credentials,
        i.e. { 'user': request.user}.
        """
        now = datetime.datetime.now(tz=utc)
        expiration = now + datetime.timedelta(minutes=10)
        new_record = {
            'code': code['code'],
            'scope': ' '.join(request.scopes),
            'client_id': client_id,
            'user': request.user['_id'],
            'expiration': expiration,
            'redirect_uri': request.redirect_uri,
        }
        self.db.authorization_codes.insert(new_record)

    # Token request

    def authenticate_client(self, request, *args, **kwargs):
        """Whichever authentication method suits you, HTTP Basic might work."""
        auth = request.headers.get('Authorization', None)
        if auth:
            auth_type, s = auth.split(' ')
            if auth_type != 'Basic':
                return False
            client_id, client_secret = decode_base64(s).split(':')
            client_id = to_unicode(client_id, 'utf-8')
            client_secret = to_unicode(client_secret, 'utf-8')

        else:
            client_id = getattr(request, 'client_id', None)
            client_secret = getattr(request, 'client_secret', None)
            if client_id is None or client_secret is None:
                return False

        client = self.get_client(client_id)
        if not client:
            return False

        request.client = client
        request.client_id = client_id

        if client.client_secret != client_secret:
            return False

        # if client.client_type != 'confidential':
        #     return False

        return True

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """Don't allow public (non-authenticated) clients."""
        raise NotImplementedError()

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """Validate the code belongs to the client.

        Add associated scopes, state and user to request.scopes, request.state
        and request.user.
        """
        record = self.db.authorization_codes.find_one({
            'code': code,
            'client_id': client.client_id,
        })
        if record is None:
            return False

        if datetime.datetime.now(tz=utc) > record['expiration']:
            return False

        request.user = record['user']
        request.scopes = record['scope'].split(' ')
        return True

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """You did save the redirect uri with the authorization code right?"""
        if redirect_uri is None:
            return True

        record = self.db.authorization_codes.find_one({
            'code': code,
            'client_id': client_id,
        })
        if record is None:
            return False

        return record['redirect_uri'] == redirect_uri

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """Clients should only be allowed to use one type of grant.

        In this case, it must be "authorization_code" or "refresh_token".
        """
        return grant_type == 'authorization_code'

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Remember to associate it with request.scopes, request.user and
        request.client.

        The two former will be set when you validate# the authorization code.
        Don't forget to save both the access_token and the refresh_token and
        set expiration for the access_token to now + expires_in seconds.
        """
        now = datetime.datetime.now(tz=utc)
        expiration = now + datetime.timedelta(seconds=token['expires_in'])
        record = {
            'access_token': token['access_token'],
            'type': token['token_type'],
            'expiration': expiration,
            'refresh_token': token.get('refresh_token'),
            'user_id': request.user,
            'scope': ' '.join(request.scopes),
            'client_id': request.client.client_id,
        }
        self.db.access_codes.insert(record)

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """Authorization codes are use once, invalidate it when a Bearer token
        has been acquired.
        """
        record = {
            'code': code,
            'client_id': request.client.client_id,
        }
        self.db.authorization_codes.remove(record)

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        """Remember to check expiration and scope membership"""
        if token is None:
            return False

        record = {
            'access_token': token,
        }
        access_code = self.db.access_codes.find_one(record)
        if access_code is None:
            return False

        if datetime.datetime.now(tz=utc) > access_code['expiration']:
            return False

        ac_scopes = access_code['scope'].split(' ')
        if not set(ac_scopes).issuperset(set(scopes)):
            return False

        request.access_token = access_code
        request.user = access_code['user_id']
        request.scopes = scopes
        request.client_id = access_code['client_id']
        request.client = self.get_client(request.client_id)

        return True

    # Token refresh request

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """Obtain the token associated with the given refresh_token and
        return its scopes, these will be passed on to the refreshed access
        token if the client did not specify a scope during the request.
        """
        raise NotImplementedError()
