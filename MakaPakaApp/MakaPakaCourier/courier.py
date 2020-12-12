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


app = Flask(__name__, static_url_path='')

db = redis.Redis(host='makapakaapp_redis-db_1',
                 port=6379, decode_responses=True)
log = app.logger
ACCESS_EXPIRATION_TIME = 60*5
SESSION_EXPIRATION_TIME = 60*5

jwt = JWTManager(app)
JWT_SECRET = os.getenv('JWT_SECRET')
app.secret_key = os.environ.get('SESSION_SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=5)
app.session_cookie_secure = True


@app.route('/')
def home():
    return {'haslo': 'tu kurier'}
