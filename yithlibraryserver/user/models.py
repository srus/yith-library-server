# Yith Library Server is a password storage server.
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

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property

from yithlibraryserver.compat import text_type
from yithlibraryserver.db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False, default='')
    last_name = Column(String, nullable=False, default='')
    screen_name = Column(String, nullable=False, default='')

    email = Column(String, nullable=False, default='')
    email_verified = Column(Boolean, nullable=False, default=False)

    date_joined = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=False)

    twitter_id = Column(String, nullable=False, default='')
    google_id = Column(String, nullable=False, default='')
    facebook_id = Column(String, nullable=False, default='')

    allow_google_analytics = Column(Boolean, nullable=False, default=False)
    send_passwords_periodically = Column(Boolean, nullable=False, default=False)

    @hybrid_property
    def full_name(self):
        result = ' '.join([self.first_name, self.last_name])
        result = result.strip()
        return result

    def __unicode__(self):
        result = self.screen_name
        if result:
            return result

        result = self.full_name
        if result:
            return result

        result = self.email
        if result:
            return result

        return text_type(self.id)

    # py3 compatibility
    def __str__(self):
        return self.__unicode__()
