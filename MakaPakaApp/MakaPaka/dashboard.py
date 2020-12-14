from flask import Flask, render_template, make_response, request, abort, session
from flask import url_for, redirect, send_file
from werkzeug.utils import secure_filename
import redis
import logging
import random
import string
import os
import os.path
from flask_jwt_extended import JWTManager
from jwt import decode, InvalidTokenError, encode
from datetime import timedelta, datetime, timezone
from model.waybill import *
import ast
from flask_cors import CORS, cross_origin


app = Flask(__name__, static_url_path='')
cors = CORS(app)
app.permanent_session_lifetime = timedelta(minutes=600)

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*600
SESSION_EXPIRATION_TIME = 60*600

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRATION_TIME
app.secret_key = os.environ.get('SESSION_SECRET_KEY')


FILES = 'files'
FILES_PATH = 'files/'

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')


def setup():
    log.setLevel(logging.DEBUG)


@app.route('/package/<string:name>')
def show_file(name):
    token = request.cookies.get('access')
    if valid(token):
        data = db.hget(FILES, name[:-4] + '_data')
        if data is None:
            abort(400)

        file_data = ast.literal_eval(data)

        waybill = to_waybill(file_data)
        path = FILES_PATH + name

        uname = session['username']
        result = db.expire('session_' + uname, SESSION_EXPIRATION_TIME)

        exp = datetime.now() + timedelta(seconds=ACCESS_EXPIRATION_TIME)
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': session['username'], 'exp': exp,
                'secret': secret}, JWT_SECRET, 'HS256'
        )
        response = make_response(redirect('https://localhost:8080/'))
        response.set_cookie(
            'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        if result == 0:
            db.srem('sessions', 'session_' + uname)

        if not os.path.exists(FILES_PATH):
            os.mkdir(FILES_PATH, 0o777)

        if not os.path.isfile(path):
            waybill.generate_and_save(filename=name[:-4], path=FILES_PATH)

        try:
            return send_file(path, attachment_filename=name)
        except Exception as e:
            log.error(e)

        return response
    else:
        abort(403)


def to_waybill(form):
    sender = to_sender(form)
    recipient = to_recipient(form)

    return Waybill(sender, recipient)


def to_sender(form):
    name = form.get('sender_name')
    surname = form.get('sender_surname')
    phone = form.get('sender_phone')
    address = to_sender_address(form)

    return Person(name, surname, address, phone)


def to_recipient(form):
    name = form.get('recipient_name')
    surname = form.get('recipient_surname')
    phone = form.get('recipient_phone')
    address = to_recipient_address(form)

    return Person(name, surname, address, phone)


def to_sender_address(form):
    sender_street = form.get('sender_street')
    sender_city = form.get('sender_city')
    sender_code = form.get('sender_code')
    sender_country = form.get('sender_country')

    addr = Address(sender_street, sender_city, sender_code, sender_country)
    return addr


def to_recipient_address(form):
    recipient_street = form.get('recipient_street')
    recipient_city = form.get('recipient_city')
    recipient_code = form.get('recipient_code')
    recipient_country = form.get('recipient_country')

    addr = Address(recipient_street, recipient_city,
                   recipient_code, recipient_country)
    return addr


def valid(token):
    try:
        decode(token, JWT_SECRET)
    except InvalidTokenError as e:
        app.logger.error(str(e))
        return False
    return True


@ app.errorhandler(400)
def bad_request(error):
    return render_template("errors/400.html", error=error)


@ app.errorhandler(401)
def page_unauthorized(error):
    return render_template("errors/401.html", error=error)


@ app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", error=error)


@ app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", error=error)


@ app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html", error=error)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
