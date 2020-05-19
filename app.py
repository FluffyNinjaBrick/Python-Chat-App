from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room
from pymongo.errors import DuplicateKeyError

from db import get_user, save_user, save_room, add_room_members, get_rooms_for_user, get_room, is_room_member, \
    get_room_members, is_room_admin, update_room, remove_room_members

app = Flask(__name__)
app.secret_key = "my secret key"
socketio = SocketIO(app)  # this encapsulates the flask app, this is what we actually run
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


# =========== ENDPOINTS =========== #
@app.route('/')
def home():
    rooms = []
    if current_user.is_authenticated:
        app.logger.info("Getting rooms...")
        rooms = get_rooms_for_user(current_user.username)
        app.logger.info(rooms)
    return render_template("index.html", rooms=rooms)


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


@app.route('/create-room', methods=['GET', 'POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        # strip removes superfluous whitespace, split splits by commas
        usernames = [username.strip() for username in request.form.get('members').split(',')]

        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)

            # if admin added himself to the list, remove him so that we don't add him twice
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for('view_room', room_id=room_id))
        else:
            message = "Failed to create room - please enter at least one person"
    return render_template('create_room.html', message=message)


@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        message = ''
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        existing_members_string = ', '.join(existing_room_members)
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['room_name'] = room_name
            update_room(room_id, room_name)
            new_members = [username.strip() for username in request.form.get('members').split(',')]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add, current_user.username)
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = 'Room edited successfully'
            existing_members_string = ", ".join(new_members)
        return render_template('edit_room.html', room=room, members_str=existing_members_string, message=message)
    else:
        return "Room not found: no such room exists or you don't have permission to edit it", 404


@app.route('/rooms/<room_id>')
@login_required
def view_room(room_id):  # this is both the view of the room and the chat itself
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        return render_template('view_room.html', room=room, room_members=room_members)
    else:
        return "Room not found", 404


# =========== EVENT HANDLERS =========== #
# this is an event handler, it handles the event emitted by the client upon connection (see view_room.html)
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


# =========== USER LOADER =========== #
@login_manager.user_loader  # needed by login_manager
def load_user(username):
    return get_user(username)


# =========== MAIN METHOD =========== #
if __name__ == '__main__':
    socketio.run(app, debug=True)
