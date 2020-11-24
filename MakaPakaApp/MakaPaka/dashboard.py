from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, jsonify, send_file, send_from_directory
import redis
import logging
import random
import string
import os
import os.path
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from jwt import decode, InvalidTokenError, encode
import datetime
from flask import send_file
from model.waybill import *
import json
import ast


app = Flask(__name__, static_url_path='')
db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*5

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRATION_TIME

FILES = 'files'
FILES_PATH = 'files/'
PATH_AND_FILENAME = 'path_and_filename'
FILENAMES = 'filenames'

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')


def setup():
    log.setLevel(logging.DEBUG)


@app.route('/packages')
def list_packages():
    token = request.cookies.get('access')
    if valid(token):
        uname = request.cookies.get('uname')
        files_code = db.hget(uname, FILES)
        packages = db.smembers(files_code)
        if len(packages) > 0:
            response = prepare_cookies('packages.html', packages=packages)
        else:
            response = prepare_cookies('packages.html')
        return response
    else:
        return """<a href='https://localhost:8080/'>Wróć do strony głównej</a>"""


@app.route('/package')
def waybill():
    token = request.cookies.get('access')
    if valid(token):
        response = prepare_cookies('addpackage.html')
        return response
    else:
        return """<a href='https://localhost:8080/'>Wróć do strony głównej</a>"""


@app.route('/addpackage', methods=['POST'])
def add_waybill():
    log.debug('Receive request to create a waybill.')
    form = request.form
    log.debug('Request form: {}.'.format(form))

    waybill = to_waybill(form)
    save_waybill(waybill, form)

    return redirect(url_for('list_packages'))


@app.route('/package/<string:name>')
def show_file(name):
    uname = request.cookies.get('access')
    uname = decode(uname, JWT_SECRET).get('uname')
    file_data = ast.literal_eval(db.hget(FILES, name[:-4] + '_data'))

    waybill = to_waybill(file_data)
    path = FILES_PATH + name
    log.debug(path)

    if not os.path.isfile(path):
        waybill.generate_and_save(filename=name[:-4], path=FILES_PATH)

    try:
        return send_file(path, attachment_filename=name)
    except Exception as e:
        log.error(e)

    return redirect(url_for('list_packages'))


@ app.route('/showdecoded')
def showJWT():
    access = request.cookies.get('access')
    secret = decode(access, JWT_SECRET)
    return secret


@ app.route('/package')
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


def save_waybill(waybill, form):
    fullname = waybill.generate_filename(path=FILES_PATH)
    filename = os.path.basename(fullname)
    log.debug('full: ' + fullname)
    log.debug('file: ' + filename)

    uname = request.cookies.get('uname')
    files = db.hget(uname, FILES)
    db.sadd(files, filename)
    db.hset(FILES, filename[:-4] + '_data', str(form.to_dict()))
    db.hset(FILES, filename[:-4] + '_date', str(datetime.datetime.utcnow()))


def valid(token):
    try:
        decode(token, JWT_SECRET)
    except InvalidTokenError as e:
        app.logger.error(str(e))
        return False
    return True


def prepare_cookies(template, packages=None):
    if packages is None:
        response = make_response(render_template(template))
    else:
        response = make_response(render_template(template, packages=packages))
    session_id = request.cookies.get('session-id')
    uname = request.cookies.get('uname')
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=ACCESS_EXPIRATION_TIME)
    secret = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(32))
    access_token = encode(
        {'uname': uname, 'exp': exp,
         'secret': secret}, JWT_SECRET, 'HS256'
    )

    response.set_cookie(
        'session-id', session_id, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
    )
    response.set_cookie(
        'uname', uname, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
    )
    response.set_cookie(
        'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
    )
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
