from flask import Flask, render_template, make_response, request
from flask import url_for, redirect
import redis
import os
from datetime import timedelta, datetime
import string
import random
from flask_jwt_extended import JWTManager
from jwt import decode, InvalidTokenError, encode


app = Flask(__name__, static_url_path='')

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')


def setup():
    log.setLevel(logging.DEBUG)


@app.route('/', methods=['GET'])
def home():
    resp = make_response(render_template('index.html'))
    resp.set_cookie('courier_access', '', max_age=-1)
    return resp


@app.route('/send')
def send(msg=None):
    return render_template('send.html', msg=msg)


@app.route('/senddata', methods=['POST'])
def senddata():
    package = request.form['package']
    locker = request.form['locker']

    if locker in db.lrange('lockers', 0, -1) and db.hget('files', package + '_status') == 'nowa':
        db.hset('files', package + '_status', 'oczekująca w paczkomacie')
        db.rpush(locker, package)
    else:
        return render_template('send.html', msg='Błędne dane! Spróbuj jeszcze raz.')

    return render_template('send.html', msg='Paczka dodana do paczkomatu')


@app.route('/takeout')
def takeout(msg=None):
    return render_template('takeout.html', msg=msg)


@app.route('/auth', methods=['POST'])
def authorize_courier():
    locker = request.form['locker']
    token = request.form['token']
    courier = None

    if db.ttl(token) > 0 and locker in db.lrange('lockers', 0, -1):
        for i in range(5):
            tokens = db.hget('courier' + str(i), 'tokens')

            if token == db.get(tokens):
                courier = 'courier' + str(i)
                break

        response = make_response(
            redirect('https://localhost:8087/packages?fromIndex=0&toIndex=4&locker=' + locker))
        exp = datetime.now() + timedelta(seconds=6000)
        secret = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        access_token = encode(
            {'uname': courier, 'exp': exp,
                'secret': secret, 'locker': locker}, JWT_SECRET, 'HS256'
        )
        response.set_cookie(
            'courier_access', access_token, max_age=600, secure=True, httponly=True
        )
        return response
    else:
        return render_template('takeout.html', msg='Błędne dane! Spróbuj jeszcze raz.')


@app.route('/packages')
def show_packages():
    token = request.cookies.get('courier_access')
    if not valid(token):
        return redirect(url_for('home'))

    fromIndex = request.args.get('fromIndex') or 0
    locker = request.args.get('locker')
    allCount = db.lrange(locker, 0, -1)
    page_count = ((len(allCount) - 1) // 5) + 1

    if page_count > 0:
        page_no = (int(fromIndex) // 5) + 1
    else:
        page_no = 0

    return render_template('packages.html', page_no=page_no, page_count=page_count)


@app.route('/GET/packages', methods=['GET'])
def getPackagesFromTo():
    token = request.cookies.get('courier_access')

    if not valid(token):
        return {}

    data = {}
    fromIndex = request.args.get('fromIndex')
    toIndex = request.args.get('toIndex')
    locker = request.args.get('locker')
    packages = db.lrange(locker, fromIndex, toIndex)
    data['packages'] = packages

    url = 'https://localhost:8087/packages?'
    prevParams = 'fromIndex=' + str(int(fromIndex) - 5) + \
        '&toIndex=' + str(int(toIndex) - 5) + '&locker=' + locker
    nextParams = 'fromIndex=' + str(int(fromIndex) + 5) + \
        '&toIndex=' + str(int(toIndex) + 5) + '&locker=' + locker

    data['prev'] = url + prevParams
    data['next'] = url + nextParams

    return data


@app.route('/POST/takepackages', methods=['POST'])
def takepackages():
    packages = request.json
    token = request.cookies.get('courier_access')
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('courier_access', '', max_age=-1)

    if not valid(token):
        return resp

    courier = decode(token, JWT_SECRET)['uname']
    packages_code = db.hget(courier, 'packages')
    locker = decode(token, JWT_SECRET)['locker']

    for package in packages:
        db.hset('files', package + '_status', 'odebrana z paczkomatu')
        db.lpush(packages_code, package)
        db.lrem(locker, 0, package)

    return resp


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
