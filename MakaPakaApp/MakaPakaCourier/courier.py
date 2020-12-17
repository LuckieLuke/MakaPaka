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


app = Flask(__name__, static_url_path='')

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')


@app.route('/')
def home():
    return render_template('main.html')


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
        return redirect('http://localhost:8085/options')

    token = decode(token, JWT_SECRET)
    package = request.form['package']

    if token['uname'] not in db.lrange('couriers', 0, -1):
        return redirect(url_for('home'))

    packages_code = token['packages']

    if db.hget('files', package + '_status') == 'nowa':
        db.rpush(packages_code, package)
        db.hset('files', package + '_status', 'przekazana kurierowi')
        db.rpush()
        return render_template('take.html', msg='Paczka odebrana!')
    else:
        return render_template('take.html', msg='Paczka nie posiada statusu "nowa"!')


@app.route('/code')
def code():
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
def authorize():
    login = request.form['login']
    password = request.form['password'].encode('utf-8')
    hashed_pass = hashlib.sha512(password).hexdigest()

    resp = make_response(redirect('http://localhost:8085/options'))
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
                'courier_login', access_token, max_age=600
            )
    return resp


@app.route('/packages')
def packages():
    token = request.cookies.get('courier_login')

    if not valid(token):
        return redirect('http://localhost:8085/')

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

    url = 'http://localhost:8085/packages?'
    prevParams = 'fromIndex=' + str(int(fromIndex) - 5) + \
        '&toIndex=' + str(int(toIndex) - 5)
    nextParams = 'fromIndex=' + str(int(fromIndex) + 5) + \
        '&toIndex=' + str(int(toIndex) + 5)

    data['prev'] = url + prevParams
    data['next'] = url + nextParams

    return data


def valid(token):
    try:
        decode(token, JWT_SECRET)
    except InvalidTokenError as _:
        return False
    return True
