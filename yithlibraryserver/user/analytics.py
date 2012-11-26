# Yith Library Server is a password storage server.
# Copyright (C) 2012 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

SESSION_KEY = 'show_google_analytics'
USER_ATTR = 'allow_google_analytics'


class GoogleAnalytics(object):

    def __init__(self, request):
        self.request = request

    @property
    def enabled(self):
        return self.request.registry.settings['google_analytics_code'] is not None

    @property
    def first_time(self):
        return SESSION_KEY not in self.request.session

    @property
    def show(self):
        user = self.request.user
        if user is None:
            return self.request.session.get(SESSION_KEY, False)
        else:
            return getattr(user, USER_ATTR, False)

    def allow(self, value):
        user = self.request.user
        if user is None:
            self.request.session[SESSION_KEY] = value
        else:
            setattr(user, USER_ATTR, value)


def get_google_analytics(request):
    return GoogleAnalytics(request)
