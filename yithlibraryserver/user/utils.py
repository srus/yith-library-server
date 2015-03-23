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

import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember

from sqlalchemy.orm.exc import NoResultFound

from yithlibraryserver.db import DBSession
from yithlibraryserver.user.models import User
from yithlibraryserver.user.providers import get_provider_key


def split_name(name):
    parts = name.split(' ')
    if len(parts) > 1:
        first_name = parts[0]
        last_name = ' '.join(parts[1:])
    else:
        first_name = parts[0]
        last_name = ''

    return first_name, last_name


def user_from_provider_id(provider, user_id):
    provider_key = get_provider_key(provider)
    column = getattr(User, provider_key)
    try:
        return DBSession.query(User).filter(column==user_id).one()
    except NoResultFound:
        return None


def register_or_update(request, provider, user_id, info, default_url='/'):
    provider_key = get_provider_key(provider)
    user = user_from_provider_id(provider, user_id)
    if user is None:

        new_info = {'provider': provider, provider_key: user_id}
        for attribute in ('screen_name', 'first_name', 'last_name', 'email'):
            if attribute in info:
                new_info[attribute] = info[attribute]
            else:
                new_info[attribute] = ''

        request.session['user_info'] = new_info
        if 'next_url' not in request.session:
            request.session['next_url'] = default_url
        return HTTPFound(location=request.route_path('register_new_user'))
    else:
        user.last_login = datetime.datetime.utcnow()

        ga = request.google_analytics
        if ga.is_in_session():
            if not ga.is_stored_in_user(user):
                user.allow_google_analytics = ga.show_in_session()
            ga.clean_session()

        user.update_user_info(info)
        DBSession.add(user)

        if 'next_url' in request.session:
            next_url = request.session['next_url']
            del request.session['next_url']
        else:
            next_url = default_url

        request.session['current_provider'] = provider
        remember_headers = remember(request, str(user.id))
        return HTTPFound(location=next_url, headers=remember_headers)
