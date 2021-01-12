from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, session, abort
import redis
import hashlib
from flask_jwt_extended import JWTManager
from jwt import decode, InvalidTokenError, encode
from datetime import timedelta, datetime
import random
import string
import os
from authlib.integrations.flask_client import OAuth


app = Flask(__name__, static_url_path='')
oauth = OAuth(app)

auth0 = oauth.register(
    'makapakaapp',
    api_base_url='https://makapaka.eu.auth0.com',
    client_id='injZ4aCCaRZqAESwn2rmuXNxqRdcHL4g',
    client_secret=os.environ.get('OAUTH_SECRET_SENDER'),
    access_token_url='https://makapaka.eu.auth0.com/oauth/token',
    authorize_url='https://makapaka.eu.auth0.com/authorize',
    client_kwargs={'scope': 'openid profile email'}
)

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*10
SESSION_EXPIRATION_TIME = 60*10

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')
app.secret_key = os.environ.get('SESSION_SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=10)
app.session_cookie_secure = True


@ app.route('/login')
def login():
    if 'username' not in session:
        return render_template('login.html', valid=True)
    else:
        return redirect('https://localhost:8080/')


@ app.route('/auth', methods=['POST'])
def auth():
    if 'username' not in session:
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
                response = make_response(
                    redirect('https://localhost:8080/'), 200)
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

        return make_response('invalid login', 404)
    else:
        return redirect('https://localhost:8080/')


@app.route('/loginoauth')
def logingoogle():
    redirect_url = url_for('authorize', _external=True)
    return auth0.authorize_redirect(redirect_url)


@app.route('/authorize')
def authorize():
    token = auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    user_info = resp.json()
    app.logger.debug(resp.json())

    hash_login = hashlib.sha512(
        user_info['nickname'].encode('utf-8')).hexdigest()
    session['username'] = hash_login
    if not db.exists(hash_login):
        file_code = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        data = {'login': hash_login, 'files': file_code, }
        db.hmset(hash_login, data)
        db.lpush('users', hash_login)

    return redirect('https://localhost:8080')
