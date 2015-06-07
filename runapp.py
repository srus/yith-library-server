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

import os

from newrelic import agent
agent.initialize()

from webob.dec import wsgify
from webob.exc import HTTPMovedPermanently

from paste.deploy import loadapp
from pyramid.paster import setup_logging
from raven.middleware import Sentry
from waitress import serve


@wsgify.middleware
def ForceTLSMiddleware(req, app):
    if 'X-Forwarded-Proto' in req.headers and req.headers['X-Forwarded-Proto'] != 'https':
        https_url = req.url.replace('http://', 'https://')
        return HTTPMovedPermanently(location=https_url)
    return req.get_response(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    scheme = os.environ.get("SCHEME", "https")
    setup_logging('yithlibraryserver/config-templates/production.ini')
    app = loadapp('config:production.ini', relative_to='yithlibraryserver/config-templates')
    app = ForceTLSMiddleware(app)
    app = Sentry(app)
    app = agent.WSGIApplicationWrapper(app)
    serve(app, host='0.0.0.0', port=port, url_scheme=scheme)
