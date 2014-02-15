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

import oauthlib.oauth2


class RequestValidator(oauthlib.oauth2.RequestValidator):

    # Pre- and post-authorization

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Simple validity check, does client exist? Not banned?"""

    def validate_redirect_url(self, client_id, redirect_url, request, *args, **kwargs):
        """Is the client allowed to use the supplied redirect_uri?
        i.e. has the client previously registered this EXACT redirect uri.
        """

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """The redirect used if none has been supplied.

        Prefer your clients to pre register a redirect uri rather than
        supplying one on each authorization request.
        """

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """Is the client allowed to access the requested scopes?"""

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """Scopes a client will authorize for if none are supplied in the
        authorization request.
        """

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """Clients should only be allowed to use one type of response type, the
        one associated with their one allowed grant type.

        In this case it must be "code".
        """

    # Post-authorization

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        """Remember to associate it with request.scopes, request.redirect_uri
        request.client, request.state and request.user

        (the last is passed in post_authorization credentials,
        i.e. { 'user': request.user}.
        """

    # Token request

    def authenticate_client(self, request, *args, **kwargs):
        """Whichever authentication method suits you, HTTP Basic might work."""

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """Don't allow public (non-authenticated) clients."""

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """Validate the code belongs to the client.

        Add associated scopes, state and user to request.scopes, request.state
        and request.user.
        """

    def confirm_redirect_uri(self, client_id, code, redirect_url, client, *args, **kwargs):
        """You did save the redirect uri with the authorization code right?"""

    def validate_grant_type(self, token, request, *args, **kwargs):
        """Clients should only be allowed to use one type of grant.

        In this case, it must be "authorization_code" or "refresh_token".
        """

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Remember to associate it with request.scopes, request.user and
        request.client.

        The two former will be set when you validate# the authorization code.
        Don't forget to save both the access_token and the refresh_token and
        set expiration for the access_token to now + expires_in seconds.
        """

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """Authorization codes are use once, invalidate it when a Bearer token
        has been acquired.
        """

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        """Remember to check expiration and scope membership"""

    # Token refresh request

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """Obtain the token associated with the given refresh_token and
        return its scopes, these will be passed on to the refreshed access
        token if the client did not specify a scope during the request.
        """
