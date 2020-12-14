from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, session, abort, jsonify
import redis
import hashlib
import logging
import random
import string
import os
from flask_jwt_extended import JWTManager
from jwt import decode, InvalidTokenError, encode
from datetime import timedelta, datetime
from model.waybill import *
from werkzeug.utils import secure_filename
import json
import uuid

app = Flask(__name__, static_url_path='')

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*600
SESSION_EXPIRATION_TIME = 60*600

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')
app.secret_key = os.environ.get('SESSION_SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=600)
app.session_cookie_secure = True

FILES = 'files'
FILES_PATH = 'files/'
PATH_AND_FILENAME = 'path_and_filename'
FILENAMES = 'filenames'


def setup():
    log.setLevel(logging.DEBUG)


# @app.after_request
# def add_headers(response):
#     log.debug('AFTER REG REQUEST')
#     response.headers["Access-Control-Allow-Origin"] = '*'
#     response.headers["Access-Control-Allow-Headers"] = '*'
#     response.headers["Access-Control-Allow-Methods"] = '*'
#     return response


@app.route('/', methods=['GET'])
def home():
    if 'username' in session:
        user = db.hget(session['username'], 'login')

        response = make_response(render_template(
            'index.html', is_logged=True, user=user))
        exp = datetime.now() + timedelta(seconds=ACCESS_EXPIRATION_TIME)
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': session['username'], 'exp': exp,
                'secret': secret}, JWT_SECRET, 'HS256'
        )
        response.set_cookie(
            'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )

        uname = session['username']
        result = db.expire('session_' + uname, SESSION_EXPIRATION_TIME)
        if result == 0:
            db.srem('sessions', 'session_' + uname)
        return response

    for session_id in db.smembers('sessions'):
        if db.get(session_id) is None:
            db.srem('sessions', session_id)

    return render_template('index.html', is_logged=False, user=None)


@ app.route('/register', methods=['GET'])
def register():
    if 'username' not in session:
        return render_template('registration.html')
    else:
        return redirect('https://localhost:8080/')


@ app.route('/user/<username>', methods=['GET'])
def checkAvailability(username):
    enc_username = username.encode('utf-8')
    hash_username = hashlib.sha512(enc_username).hexdigest()
    users = db.lrange('users', 0, -1)
    if hash_username not in users:
        return make_response('go on', 404)
    else:
        return make_response('wait', 200)


@app.route("/package/delete/<string:name>", methods=["DELETE"])
def delete(name):
    if 'username' in session:
        for field in ('_data', '_date', '_status'):
            db.hdel(FILES, name[:-4] + field)

        files = db.hget(session['username'], FILES)
        db.lrem(files, 0, name)

        if os.path.exists(FILES_PATH + name):
            os.remove(FILES_PATH + name)
        if os.path.exists(FILES_PATH + name[:-4] + '.png'):
            os.remove(FILES_PATH + name[:-4] + '.png')
        if os.path.exists(FILES_PATH + name[:-4] + '.jpeg'):
            os.remove(FILES_PATH + name[:-4] + '.jpeg')

    return redirect(url_for("getPackagesFromTo", fromIndex=0, toIndex=3))


@ app.route('/create', methods=['POST'])
def createUser():
    if 'username' not in session:
        login = request.form['login']
        enc_login = login.encode('utf-8')
        hash_login = hashlib.sha512(enc_login).hexdigest()
        password = request.form['password'].encode('utf-8')
        hash_pass = hashlib.sha512(password).hexdigest()
        pesel = request.form['pesel']
        name = request.form['name']
        surname = request.form['surname']
        birthdate = request.form['birthdate']
        city = request.form['city']
        street = request.form['street']
        number = request.form['number']
        postcode = request.form['postcode']
        country = request.form['country']
        file_code = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        data = {'login': login, 'password': hash_pass, 'files': file_code,
                'pesel': pesel, 'name': name, 'surname': surname,
                'birthdate': birthdate, 'city': city, 'street': street,
                'number': number, 'postcode': postcode, 'country': country}
        db.hmset(hash_login, data)
        db.lpush('users', hash_login)
        return redirect(url_for('home')), 200
    else:
        return redirect(url_for('home')), 404


@ app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        response = make_response(redirect(url_for('home')))
        uname = session['username']
        db.srem('sessions', 'session_' + uname)

        session.clear()
        response.set_cookie('access', '', max_age=0,
                            secure=True, httponly=True)
        return response
    else:
        redirect(url_for('home'))


@app.route('/packages')
def list_packages():
    if 'username' in session:
        uname = session['username']
        files_code = db.hget(uname, FILES)
        packages_names = db.lrange(files_code, 0, -1)
        num = len(packages_names)
        packages = []
        for package in packages_names:
            shortname = package[:-4]
            date = (db.hget('files', shortname + '_date'))[:-7]
            packages.append((package, date))

        if len(packages) > 0:
            response = prepare_cookies(
                'packages.html', packages=packages, number=num
            )
        else:
            response = prepare_cookies('packages.html')
        return response
    else:
        abort(403)


@app.route('/GET/packages', methods=['GET'])
def getPackagesFromTo():
    if 'username' in session:
        fromIndex = request.args.get('fromIndex')
        toIndex = request.args.get('toIndex')
        access = db.hget(session['username'], 'files')

        files = db.lrange(access, fromIndex, toIndex)
        full_files_data = {}
        for f in files:
            shortname = f[:-4]
            date = (db.hget('files', shortname + '_date'))[:-7]
            status = db.hget('files', shortname + '_status')
            if not status:
                status = 'nowa'
            full_files_data[f] = (f, date, status)

        url = 'https://localhost:8080/packages?'
        prevParams = 'fromIndex=' + str(int(fromIndex) - 4) + \
            '&toIndex=' + str(int(toIndex) - 4)
        nextParams = 'fromIndex=' + str(int(fromIndex) + 4) + \
            '&toIndex=' + str(int(toIndex) + 4)

        full_data = {}
        full_data['files'] = full_files_data
        full_data['prev'] = url + prevParams
        full_data['next'] = url + nextParams

        return full_data
    return redirect('https://localhost:8080/')


@app.route('/package')
def waybill():
    token = request.cookies.get('access')
    if valid(token):
        response = prepare_cookies('addpackage.html')
        return response

    return redirect('https://localhost:8080/')


@app.route('/addpackage', methods=['POST'])
def add_waybill():
    log.debug('Receive request to create a waybill.')
    form = request.form
    log.debug('Request form: {}.'.format(form))

    waybill = to_waybill(form)
    save_waybill(waybill, form)

    return redirect('https://localhost:8080/packages?fromIndex=0&toIndex=3')


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

    token = request.cookies.get('access')
    uname = decode(token, JWT_SECRET).get('uname')
    files = db.hget(uname, FILES)
    db.lpush(files, filename)
    db.hset(FILES, filename[:-4] + '_data', str(form.to_dict()))
    db.hset(FILES, filename[:-4] + '_date',
            str(datetime.now() + timedelta(hours=1)))


def valid(token):
    try:
        decode(token, JWT_SECRET)
    except InvalidTokenError as e:
        return False
    return True


def prepare_cookies(template, packages=None, number=None):
    response = make_response(render_template(
        template, packages=packages, number=number))
    exp = datetime.now() + timedelta(seconds=ACCESS_EXPIRATION_TIME)
    token = request.cookies.get('access')
    if token is not None:
        uname = decode(token, JWT_SECRET).get('uname')
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': uname, 'exp': exp,
                'secret': secret}, JWT_SECRET, 'HS256'
        )
        response.set_cookie(
            'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )

        result = db.expire('session_' + uname, SESSION_EXPIRATION_TIME)
        if result == 0:
            db.srem('sessions', 'session_' + uname)

    for session_id in db.smembers('sessions'):
        if db.get(session_id) is None:
            db.srem('sessions', session_id)
    return response


@app.errorhandler(400)
def bad_request(error):
    return render_template("errors/400.html", error=error)


@app.errorhandler(401)
def page_unauthorized(error):
    return render_template("errors/401.html", error=error)


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", error=error)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", error=error)


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html", error=error)


@app.route('/decode')
def getInfo():
    access_token = request.cookies.get('access')
    info = decode(access_token, JWT_SECRET)
    return info


@app.route('/generate')
def generate():
    couriers = db.lrange('couriers', 0, -1)
    if len(couriers) == 0:
        for i in range(5):
            name = 'kurier' + str(i)
            hashed = hashlib.sha512(name.encode('utf-8')).hexdigest()

            data = {}
            data['username'] = hashed
            data['password'] = hashed
            data['packages'] = uuid.uuid4().hex
            db.lpush('couriers', hashed)
            db.hmset(hashed, data)

    lockers = db.lrange('lockers', 0, -1)
    if len(lockers) == 0:
        for i in range(5):
            idf = 'locker' + str(i)

            data = {}
            data['packages'] = uuid.uuid4().hex
            data['tokens'] = uuid.uuid4().hex
            db.lpush('lockers', idf)
            db.hmset(idf, data)

    return redirect('https://localhost:8080/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
