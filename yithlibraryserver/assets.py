# Yith Library Server is a password storage server.
# Copyright (C) 2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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

from webassets import Bundle

yithlibrary_css = Bundle(
    'css/bootstrap-3.3.0.css',
    'css/style.css',
    filters='cleancss',
    output='build/yithlibrary.%(version)s.css',
)

yithlibrary_js = Bundle(
    'js/libs/jquery-2.1.1.js',
    'js/libs/bootstrap-3.3.0.js',
    'js/jquery.banner.js',
    'js/jquery.checkAll.js',
    'js/jquery.confirmForm.js',
    'js/jquery.emailVerificationButton.js',
    'js/jquery.googleAnalyticsPreferenceForm.js',
    'js/jquery.persona.js',
    'js/jquery.wizard.js',
    'js/app.js',
    filters='rjsmin',
    output='build/yithlibrary.%(version)s.js',
)


def includeme(config):
    config.add_webasset('yithlibrary_css', yithlibrary_css)
    config.add_webasset('yithlibrary_js', yithlibrary_js)
