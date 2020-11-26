from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, session
import redis
import hashlib
import logging
import random
import string
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from jwt import encode
from datetime import timedelta, datetime


app = Flask(__name__, static_url_path='')
app.secret_key = b'weknni34fcc#x39cb20xcme/d3983dn-'
app.permanent_session_lifetime = timedelta(minutes=5)
app.session_cookie_secure = True

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*5

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')


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
        return response

    return render_template('index.html', is_logged=False, user=None)


@ app.route('/register', methods=['GET'])
def register():
    return render_template('registration.html')


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
    return render_template('login.html', valid=True)


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
            now = str(datetime.now() + timedelta(hours=1))[:-7]
            db.hset(hashed_login, 'last_login', now)

            return response

    return render_template('login.html', valid=False)


@ app.route('/logout', methods=['GET', 'POST'])
def logout():
    response = make_response(redirect(url_for('home')))
    session.clear()
    response.set_cookie('access', '', max_age=0, secure=True, httponly=True)
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
