from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit, send

app = Flask(__name__)
socket_io = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def home():
    return {'msg': 'hejka'}


@socket_io.on('connect')
def handle_on_connect():
    app.logger.debug('Connected')


@socket_io.on('join')
def handle_on_join(data):
    useragent = data['useragent']
    room_id = data['room_id']
    join_room(room_id)
    app.logger.debug('JOINED %s' % (useragent))
    emit('joined_room', {'room_id': room_id})


@socket_io.on('putin')
def handle_on_put(data):
    useragent = data['useragent']
    app.logger.debug(data['package_id'])
    emit('put_in_locker', {
        'package_id': data['package_id'],
        'locker_id': data['locker_id'],
    }, room=data['package_id'])


@socket_io.on('putout')
def handle_on_take(data):
    app.logger.debug(data['package_id'])
    emit('take_from_locker', {
        'package_id': data['package_id']
    }, room=data['package_id'])


@socket_io.on('take_from_sender')
def handle_on_take_from_sender(data):
    emit('take_from_sender', {
        'package_id': data['package_id']
    }, room=data['package_id'])


@socket_io.on('new_package')
def handle_on_new_package(data):
    useragent = data['useragent']
    app.logger.debug('refreshing')
    emit('refresh_packages', {
        'room_id': data['room_id']
    }, room=data['room_id'])
