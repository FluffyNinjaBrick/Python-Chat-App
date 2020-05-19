from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room
from pymongo.errors import DuplicateKeyError

from db import get_user, save_user

app = Flask(__name__)
app.secret_key = "my secret key"
socketio = SocketIO(app)  # this encapsulates the flask app, this is what we actually run
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    return render_template("index.html")


# GET - go to login form, POST - submit form data
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login!'
    return render_template('login.html', message=message)


@app.route('/logout')
@login_required  # this causes an unauthenticated user that tries to access /logout to be redirected to /login
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user(username)
        try:
            save_user(username, email, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = "User already exists!"
    return render_template('signup.html', message=message)


@app.route('/chat')
@login_required
def chat():
    # get the username and chatroom number from the get request generated by the form
    username = request.args.get('username')
    room = request.args.get('room')

    # if they are correct, we enter the chatroom; the parameters can be accessed in the template via {{}}
    if username and room:
        return render_template('chat.html', username=username, room=room)
    # if not, we redirect to home( / )
    else:
        return redirect(url_for('home'))


# this is an event handler, it handles the event emitted by the client upon connection (see chat.html)
@socketio.on('join-room')
def handle_join_room_event(data):
    app.logger.info("user {} has joined room {}".format(data['username'], data['room']))
    join_room(data['room'])  # socketIO has a default room system, which we will use
    socketio.emit('join-room-announcement', data)


@socketio.on('leave-room')
def handle_join_room_event(data):
    app.logger.info("user {} has left room {}".format(data['username'], data['room']))
    # sockets leave rooms automatically upon disconnection, no further action needed
    socketio.emit('leave-room-announcement', data)


@socketio.on('send-message')
def handle_send_message(data):
    app.logger.info("{}'s message in room {}: {}".format(data['username'], data['room'], data['message']))
    socketio.emit('receive-message', data, room=data['room'])


@login_manager.user_loader  # needed by login_manager
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
