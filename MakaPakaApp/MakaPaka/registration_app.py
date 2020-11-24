from flask import Flask, render_template, make_response, request
from flask import url_for, redirect
import redis
import hashlib
import logging
import random
import string
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from jwt import encode
import datetime


app = Flask(__name__, static_url_path='')
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
    session_id = request.cookies.get('session-id')
    uname = request.cookies.get('uname')
    user = None
    if uname is not None:
        user = db.hget(uname, 'login')

    if session_id is not None:
        response = make_response(render_template(
            'index.html', is_logged=True, user=user))
        exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=ACCESS_EXPIRATION_TIME)
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': uname, 'exp': exp,
                'secret': secret}, JWT_SECRET, 'HS256'
        )
        response.set_cookie(
            'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        response.set_cookie(
            'session-id', session_id, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        response.set_cookie(
            'uname', uname, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        return response
    else:
        return render_template('index.html', is_logged=False, user=None)


@ app.route('/register', methods=['GET'])
def register():
    return render_template('registration.html')


@ app.route('/user/<username>', methods=['GET'])
def checkAvailability(username):
    enc_username = username.encode('utf-8')
    hash_username = hashlib.sha512(enc_username).hexdigest()
    exists = db.hgetall(hash_username)
    if len(exists) == 0:
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
    data = {'session_id': hash_login, 'login': login, 'password': hash_pass, 'files': file_code,
            'pesel': pesel, 'name': name, 'surname': surname,
            'birthdate': birthdate, 'city': city, 'street': street,
            'number': number, 'postcode': postcode, 'country': country}
    db.hmset(hash_login, data)
    return redirect(url_for("home")), 200


@ app.route('/login')
def login():
    return render_template('login.html')


@ app.route('/auth', methods=['POST'])
def authorize():
    login = request.form['login'].encode('utf-8')
    hashed_login = hashlib.sha512(login).hexdigest()
    password = request.form['password'].encode('utf-8')
    hashed_pass = hashlib.sha512(password).hexdigest()
    correct_password = db.hget(hashed_login, 'password')
    if hashed_pass == correct_password:
        session_id = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(128))
        db.hset(hashed_login, 'session_id', session_id)
        response = make_response(redirect(url_for('home')))
        response.set_cookie(
            'session-id', session_id, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        response.set_cookie(
            'uname', hashed_login, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )

        exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=ACCESS_EXPIRATION_TIME)
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': hashed_login, 'exp': exp,
                'secret': secret}, JWT_SECRET, 'HS256'
        )
        response.set_cookie(
            'access', access_token, max_age=ACCESS_EXPIRATION_TIME, secure=True, httponly=True
        )
        return response
    else:
        return render_template('login.html')


@ app.route('/logout', methods=['GET', 'POST'])
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('session-id', '', max_age=0,
                        secure=True, httponly=True)
    response.set_cookie('uname', '', max_age=0,
                        secure=True, httponly=True)
    response.set_cookie('access', '', max_age=0, secure=True, httponly=True)
    return response


@ app.route('/getuser/<username>')
def getUser(username):
    return db.hgetall(username)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
