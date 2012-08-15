from pyramid.renderers import render

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message


class EmailVerificationCode(object):

    def __init__(self, code=None):
        if code is None:
            self.code = self._generate_code()
        else:
            self.code = code

    def _generate_code(self):
        return '1234'

    def store(self, db, user):
        result = db.users.update({'_id': user['_id']}, {
                '$set': {'email_verification_code': self.code},
                }, safe=True)
        return result['n'] == 1

    def remove(self, db, email, verified):
        result = db.users.update({
                'email_verification_code': self.code,
                'email': email,
                }, {
                '$unset': {'email_verification_code': 1},
                '$set': {'email_verified': verified},
                }, safe=True)
        return result['n'] == 1

    def verify(self, db, email):
        result = db.users.find_one({
                'email': email,
                'email_verification_code': self.code,
                })
        return result is not None

    def send(self, request, user):
        link = request.route_url('user_verify_email')
        link += '?code=%s&email=%s' % (self.code, user['email'])
        body = render('yithlibraryserver.user:templates/email_verification_code.txt',
                      {'link': link, 'user': user},
                      request=request)
        message = Message(subject='Please verify your email address',
                          recipients=user['email'],
                          body=body)

        get_mailer(request).send(message)
