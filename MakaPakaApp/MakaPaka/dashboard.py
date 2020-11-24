from flask import Flask, render_template, make_response, request, abort
from flask import url_for, redirect, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
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
        packages_names = db.smembers(files_code)
        num = len(packages_names)
        packages = []
        for package in packages_names:
            shortname = package[:-4]
            date = (db.hget('files', shortname + '_date'))[:-7]
            packages.append((package, date))

        if len(packages) > 0:
            response = prepare_cookies(
                'packages.html', packages=packages, number=num)
        else:
            response = prepare_cookies('packages.html')
        return response
    else:
        abort(403)


@app.route('/package')
def waybill():
    token = request.cookies.get('access')
    if valid(token):
        response = prepare_cookies('addpackage.html')
        return response
    else:
        return redirect('https://localhost:8080/')


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

    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            photo_name = secure_filename(photo.filename).split('.')
            photo_name[0] = filename[:-4]
            photo_name = '.'.join(photo_name)
            photo.save(os.path.join(FILES_PATH, photo_name))

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


def prepare_cookies(template, packages=None, number=None):
    if packages is None:
        response = make_response(render_template(template))
    else:
        response = make_response(render_template(
            template, packages=packages, number=number))
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


@app.errorhandler(401)
def page_unauthorized(error):
    return render_template("errors/401.html", error=error)


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", error=error)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", error=error)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
