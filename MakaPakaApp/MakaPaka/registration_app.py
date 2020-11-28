from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, session, abort
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


app = Flask(__name__, static_url_path='')
app.secret_key = b'weknni34fcc#x39cb20xcme/d3983dn-'
app.permanent_session_lifetime = timedelta(minutes=5)
app.session_cookie_secure = True

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*5
SESSION_EXPIRATION_TIME = 60*5

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')

FILES = 'files'
FILES_PATH = 'files/'
PATH_AND_FILENAME = 'path_and_filename'
FILENAMES = 'filenames'


def setup():
    log.setLevel(logging.DEBUG)


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
    if not 'username' in session:
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


@ app.route('/create', methods=['POST'])
def createUser():
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
    return redirect(url_for("home")), 200


@ app.route('/login')
def login():
    if not 'username' in session:
        return render_template('login.html', valid=True)
    else:
        return redirect('https://localhost:8080/')


@ app.route('/auth', methods=['POST'])
def authorize():
    login = request.form['login'].encode('utf-8')
    hashed_login = hashlib.sha512(login).hexdigest()
    users = db.lrange('users', 0, -1)

    if hashed_login in users:
        password = request.form['password'].encode('utf-8')
        hashed_pass = hashlib.sha512(password).hexdigest()
        correct_password = db.hget(hashed_login, 'password')
        if hashed_pass == correct_password:
            session['username'] = hashed_login
            session.permanent = True
            response = make_response(redirect(url_for('home')))
            exp = datetime.now() + timedelta(seconds=ACCESS_EXPIRATION_TIME)
            secret = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for _ in range(32))
            access_token = encode(
                {'uname': hashed_login, 'exp': exp,
                    'secret': secret}, JWT_SECRET, 'HS256'
            )
            response.set_cookie(
                'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
            )

            db.sadd('sessions', 'session_' + hashed_login)
            db.set('session_' + hashed_login, 'active')
            db.expire('session_' + hashed_login, SESSION_EXPIRATION_TIME)

            now = str(datetime.now() + timedelta(hours=1))[:-7]
            db.hset(hashed_login, 'last_login', now)

            return response

    return render_template('login.html', valid=False)


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
        packages_names = db.smembers(files_code)
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

    return redirect(url_for('list_packages'))


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

    token = request.cookies.get('access')
    uname = decode(token, JWT_SECRET).get('uname')
    files = db.hget(uname, FILES)
    db.sadd(files, filename)
    db.hset(FILES, filename[:-4] + '_data', str(form.to_dict()))
    db.hset(FILES, filename[:-4] + '_date',
            str(datetime.now() + timedelta(hours=1)))


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
        exp = datetime.now() + timedelta(seconds=ACCESS_EXPIRATION_TIME)
        token = request.cookies.get('access')
        if token:
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
