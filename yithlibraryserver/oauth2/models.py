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

from datetime import datetime

from pyramid_sqlalchemy import BaseObject

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, backref


class Application(BaseObject):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    creation = Column(DateTime, nullable=False, default=datetime.utcnow)
    modification = Column(DateTime, nullable=False, onupdate=datetime.utcnow)

    main_url = Column(String, nullable=False, default='')
    callback_url = Column(String, nullable=False, default='')
    authorized_origins = Column(ARRAY(String), nullable=True)

    client_id = Column(String, nullable=False, default='')
    client_secret = Column(String, nullable=False, default='')

    image_url = Column(String, nullable=False, default='')
    description = Column(Text, nullable=False, default='')

    production_ready = Column(Boolean, nullable=False, default=False)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref=backref('applications'))#, order_by='id'))


class AuthorizedApplication(BaseObject):
    __tablename__ = 'authorized_applications'

    id = Column(Integer, primary_key=True)
    scope = Column(ARRAY(String), nullable=True)
    response_type = Column(String, nullable=False, default='')
    redirect_uri = Column(String, nullable=False, default='')

    application_id = Column(
        Integer,
        ForeignKey('applications.id'),
        nullable=False,
    )
    application = relationship(
        'Application',
        backref=backref('authorized_applications'), #, order_by='id'),
    )

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
    )
    user = relationship(
        'User',
        backref=backref('authorized_applications'), #, order_by='id'),
    )


class AuthorizationCode(BaseObject):
    __tablename__ = 'authorization_codes'

    code = Column(String, primary_key=True)
    creation = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiration = Column(DateTime, nullable=False)

    scope = Column(ARRAY(String), nullable=True)
    redirect_uri = Column(String, nullable=False, default='')

    application_id = Column(
        Integer,
        ForeignKey('applications.id'),
        nullable=False,
    )
    application = relationship(
        'Application',
        backref=backref('authorization_codes'), #, order_by='creation'),
    )

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
    )
    user = relationship(
        'User',
        backref=backref('authorization_codes'), #, order_by='creation'),
    )


class AccessCode(BaseObject):
    __tablename__ = 'access_codes'

    code = Column(String, primary_key=True)
    creation = Column(DateTime, nullable=False, default=datetime.utcnow)

    scope = Column(ARRAY(String), nullable=True)

    application_id = Column(
        Integer,
        ForeignKey('applications.id'),
        nullable=False,
    )
    application = relationship(
        'Application',
        backref=backref('access_codes'), #, order_by='creation'),
    )

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
    )
    user = relationship(
        'User',
        backref=backref('access_codes'), #, order_by='creation'),
    )
