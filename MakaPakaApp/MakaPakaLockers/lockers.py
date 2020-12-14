from flask import Flask, render_template, make_response, request
from flask import url_for, redirect
import redis


app = Flask(__name__, static_url_path='')

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/send')
def send():
    return render_template('send.html')


@app.route('/takeout')
def takeout():
    return render_template('takeout.html')
