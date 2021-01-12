from flask import Flask, render_template, make_response, request
from flask import url_for, redirect, session, abort
import redis
import uuid
from flask_jwt_extended import JWTManager
from jwt import decode, InvalidTokenError, encode
import os
import hashlib
import datetime
from datetime import timedelta, datetime
import string
import random
from authlib.integrations.flask_client import OAuth


app = Flask(__name__, static_url_path='')
oauth = OAuth(app)

auth0 = oauth.register(
    'makapakaapp',
    api_base_url='https://makapaka.eu.auth0.com',
    client_id='I2UWn9Woc1WYFYt02oP0mlpxIpeSEkiK',
    client_secret='s56-ibhxFRf56YQTkaJz6kupgj-wdBAPnoBNIKgv3eyYmLuoXq_FKl799mn2Vv38',
    access_token_url='https://makapaka.eu.auth0.com/oauth/token',
    authorize_url='https://makapaka.eu.auth0.com/authorize',
    client_kwargs={'scope': 'openid profile email'}
)

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')
app.secret_key = 'nou2fdi47hicmxxx43h9xh92h7972hksj39'


@app.route('/')
def home(msg=None):
    return render_template('main.html', msg=msg)


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')


@app.route('/options')
def options():
    token = request.cookies.get('courier_login')

    if not valid(token) or decode(token, JWT_SECRET)['uname'] not in db.lrange('couriers', 0, -1):
        return redirect(url_for('home'))

    return render_template('options.html')


@app.route('/take')
def take(msg=None):
    token = request.cookies.get('courier_login')

    if not valid(token):
        return redirect(url_for('home'))

    return render_template('take.html', msg=msg)


@app.route('/takepackage', methods=['POST'])
def take_package():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return redirect('https://localhost:8085/')

    token = decode(token, JWT_SECRET)
    package = request.form['package']

    if token['uname'] not in db.lrange('couriers', 0, -1):
        return redirect(url_for('home'))

    packages_code = token['packages']

    if db.hget('files', package + '_status') == 'nowa':
        db.lpush(packages_code, package)
        db.hset('files', package + '_status', 'przekazana kurierowi')
        return make_response({'package': package}, 200)
    else:
        return make_response({'package': package}, 404)


@app.route('/code')
def code():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return redirect(url_for('home'))
    return render_template('code.html')


@app.route('/GET/code', methods=['GET'])
def generate():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return {'code': 'Zaloguj się!'}

    courier = decode(token, JWT_SECRET)['uname']
    tokens_code = db.hget(courier, 'tokens')
    code = (uuid.uuid4().hex)[0:8]

    db.set(tokens_code, code)
    db.set(code, code)
    db.expire(code, 60)

    return {'code': code}


@app.route('/auth', methods=['POST'])
def auth():
    login = request.form['login']
    password = request.form['password'].encode('utf-8')
    hashed_pass = hashlib.sha512(password).hexdigest()

    resp = make_response(redirect('https://localhost:8085/options'))
    if login in db.lrange('couriers', 0, -1):
        correct_pass = db.hget(login, 'password')
        if correct_pass == hashed_pass:
            exp = datetime.now() + timedelta(seconds=600)
            secret = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for _ in range(32))
            access_token = encode(
                {'uname': login, 'exp': exp,
                 'secret': secret, 'packages': db.hget(login, 'packages')}, JWT_SECRET, 'HS256'
            )
            resp.set_cookie(
                'courier_login', access_token, max_age=600, secure=True, httponly=True
            )
            return resp
        return render_template('main.html', msg='Błędne dane logowania!')
    return render_template('main.html', msg='Błędne dane logowania!')


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

    name = resp.json()['nickname']

    if name not in db.lrange('couriers', 0, -1):
        data = {}
        data['username'] = name
        data['packages'] = uuid.uuid4().hex
        data['tokens'] = uuid.uuid4().hex
        db.lpush('couriers', name)
        db.hmset(name, data)

    exp = datetime.now() + timedelta(seconds=600)
    secret = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(32))
    access_token = encode(
        {'uname': name, 'exp': exp,
         'secret': secret, 'packages': db.hget(name, 'packages')}, JWT_SECRET, 'HS256'
    )
    resp = make_response(redirect(url_for('options')))
    resp.set_cookie(
        'courier_login', access_token, max_age=600, secure=True, httponly=True
    )
    return resp


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie(
        'courier_login', '', max_age=-1, secure=True, httponly=True
    )
    return resp


@app.route('/packages')
def packages():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return redirect('https://localhost:8085/')

    token = decode(token, JWT_SECRET)
    packages_code = token['packages']

    fromIndex = request.args.get('fromIndex') or 0
    allCount = db.lrange(packages_code, 0, -1)
    page_count = ((len(allCount) - 1) // 5) + 1

    if page_count > 0:
        page_no = (int(fromIndex) // 5) + 1
    else:
        page_no = 0

    return render_template('packages.html', page_no=page_no, page_count=page_count)


@app.route('/GET/packages')
def packagesFromTo():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return {}

    token = decode(token, JWT_SECRET)
    packages_code = token['packages']

    data = {}
    fromIndex = request.args.get('fromIndex')
    toIndex = request.args.get('toIndex')
    packages = db.lrange(packages_code, fromIndex, toIndex)
    data['packages'] = packages

    url = 'https://localhost:8085/packages?'
    prevParams = 'fromIndex=' + str(int(fromIndex) - 5) + \
        '&toIndex=' + str(int(toIndex) - 5)
    nextParams = 'fromIndex=' + str(int(fromIndex) + 5) + \
        '&toIndex=' + str(int(toIndex) + 5)

    data['prev'] = url + prevParams
    data['next'] = url + nextParams

    return data


@app.route('/GET/uname')
def get_uname():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return make_response({'uname': 'nobody'}, 404)

    token = decode(token, JWT_SECRET)
    return make_response({'uname': token['uname']}, 200)


def valid(token):
    try:
        decode(token, JWT_SECRET)
    except InvalidTokenError as _:
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
