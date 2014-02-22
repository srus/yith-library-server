# Yith Library Server is a password storage server.
# Copyright (C) 2012-2013 Yaco Sistemas
# Copyright (C) 2012-2013 Alejandro Blanco Escudero <alejandro.b.e@gmail.com>
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

import binascii

import requests

from pyramid.httpexceptions import HTTPUnauthorized

from yithlibraryserver.compat import text_type


def get_user_info(settings, user_id):
    # Get a bearer token
    token_url = settings['twitter_bearer_token_url']
    key = settings['twitter_consumer_key']
    secret = settings['twitter_consumer_secret']
    auth = key + ':' + secret
    auth = 'Basic ' + text_type(binascii.b2a_base64(auth.encode('ascii'))[:-1],
                                'ascii')

    response = requests.post(
        token_url,
        headers={
            'Authorization': auth.encode('ascii'),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
        data='grant_type=client_credentials',
    )
    if not response.ok:
        raise HTTPUnauthorized(response.text)

    data = response.json()
    assert data['token_type'] == 'bearer'
    access_token = data['access_token']

    # Call the user info rest API
    user_info_url = settings['twitter_user_info_url']

    response = requests.get(
        user_info_url,
        params={'user_id': user_id},
        headers={'Authorization': 'Bearer ' + access_token},
    )

    if not response.ok:
        raise HTTPUnauthorized(response.text)

    return response.json()
