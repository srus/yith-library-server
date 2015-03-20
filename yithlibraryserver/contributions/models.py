# Yith Library Server is a password storage server.
# Copyright (C) 2013-2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
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
from bson.tz_util import utc

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from yithlibraryserver.db import Base

class Donation(Base):
    __tablename__ = 'donations'

    id = Column(Integer, primary_key=True)
    creation = Column(DateTime, nullable=False, default=datetime.utcnow)
    modification = Column(DateTime, nullable=False, onupdate=datetime.utcnow)

    first_name = Column(String, nullable=False, default='')
    last_name = Column(String, nullable=False, default='')

    email = Column(String, nullable=False, default='')

    street = Column(String, nullable=False, default='')
    city = Column(String, nullable=False, default='')
    zipcode = Column(String, nullable=False, default='')
    state = Column(String, nullable=False, default='')
    country = Column(String, nullable=False, default='')

    amount = Column(Integer, nullable=False)
    send_sticker = Column(Boolean, nullable=False, default=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref=backref('passwords', order_by='id'))


def include_sticker(amount):
    return amount > 1


def create_donation(request, data):
    amount = int(data['amount'])
    donation = {
        'amount': amount,
        'firstname': data['firstname'],
        'lastname': data['lastname'],
        'city': data['city'],
        'country': data['country'],
        'state': data['state'],
        'street': data['street'],
        'zip': data['zip'],
        'email': data['email'],
        'creation': datetime.now(tz=utc),
    }
    if include_sticker(amount):
        donation['send_sticker'] = not ('no-sticker' in data)
    else:
        donation['send_sticker'] = False

    if request.user is not None:
        donation['user'] = request.user['_id']
    else:
        donation['user'] = None

    _id = request.db.donations.insert(donation)
    donation['_id'] = _id
    return donation
