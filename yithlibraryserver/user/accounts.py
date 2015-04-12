# Yith Library Server is a password storage server.
# Copyright (C) 2012-2013 Yaco Sistemas
# Copyright (C) 2012-2013 Alejandro Blanco Escudero <alejandro.b.e@gmail.com>
# Copyright (C) 2012-2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

from pyramid_sqlalchemy import Session
from sqlalchemy.orm.exc import NoResultFound

from yithlibraryserver.email import send_email_to_admins
from yithlibraryserver.user.models import User
from yithlibraryserver.user.providers import get_available_providers



def merge_accounts(master_user, accounts):
    merged = 0

    for account in accounts:
        user_id = account
        if master_user.id == user_id:
            continue

        try:
            current_user = Session.query(User).filter(User.id==user_id).one()
        except NoResultFound:
            continue

        merge_users(master_user, current_user)

        merged += 1

    return merged


def merge_users(user1, user2):
    # move all passwords of user2 to user1
    db.passwords.update({'owner': user2['_id']}, {
        '$set': {
            'owner': user1['_id'],
        },
    }, multi=True)

    # move authorized_apps from user2 to user1
    authorizator = Authorizator(db)
    for auth in authorizator.get_user_authorizations(user2):
        credentials = {
            'client_id': auth['client_id'],
            'user': user1,
            'redirect_uri': auth['redirect_uri'],
            'response_type': auth['response_type'],
        }
        scopes = auth['scope'].split(' ')
        authorizator.store_user_authorization(scopes, credentials)
    authorizator.remove_all_user_authorizations(user2)

    updates = {}
    # copy the providers
    for provider in get_available_providers():
        key = provider + '_id'
        if key in user2 and key not in user1:
            sets = updates.setdefault('$set', {})
            sets[key] = user2[key]

    db.users.update({'_id': user1['_id']}, updates)

    # remove user2
    db.users.remove(user2['_id'])


def notify_admins_of_account_removal(request, user, reason):
    context = {
        'reason': reason or 'no reason was given',
        'user': user,
        'home_link': request.route_url('home'),
    }
    return send_email_to_admins(
        request,
        'yithlibraryserver.user:templates/account_removal_notification',
        context,
        'A user has destroyed his Yith Library account',
    )
