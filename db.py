from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient, DESCENDING, ASCENDING
from werkzeug.security import generate_password_hash

from user import User

# USER:        _id, email, password (hashed)
# ROOM:        _id, room_name, created_by, created_at
# ROOM MEMBER: _id: {room_id, username}, room_name, added_by, added_at, is_admin
# MESSAGE:     _id, room_id, text, sender, created_at


client = MongoClient("mongodb+srv://FluffyNinjaBrick:Marcjanin123@dblab-lnoyu.mongodb.net/test?retryWrites=true&w=majority")

chat_db = client.get_database('ChatDB')
users_collection = chat_db.get_collection("users")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")
messages_collection = chat_db.get_collection("messages")


# =========== USER METHODS =========== #
def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({'_id': username, 'email': email, 'password': password_hash})


def get_user(username):
    user_data = users_collection.find_one({'_id': username})
    # return a new User object if the user exists in the DB, else none
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None


# =========== ROOM METHODS =========== #
def save_room(room_name, created_by):
    room_id = rooms_collection.insert_one(
        {'room_name': room_name,
         'created_by': created_by,
         'created_at': datetime.now()
         }).inserted_id
    add_room_member(room_id, room_name, created_by, created_by, is_admin=True)
    return room_id


def get_room(room_id):
    # we have the ID as a string, we need to cast it to ObjectID
    return rooms_collection.find_one({'_id': ObjectId(room_id)})


def update_room(room_id, room_name):
    # update name in room
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {'room_name': room_name}})
    # update name in members
    room_members_collection.update_many({'_id.room_id': ObjectId(room_id)}, {'$set': {'room_name': room_name}})


def delete_room(room_id):
    members = get_room_members(ObjectId(room_id))
    print(members)
    remove_room_members(ObjectId(room_id), [member['_id']['username'] for member in members])
    rooms_collection.remove(ObjectId(room_id))


def get_rooms_for_user(username):
    return [room for room in room_members_collection.find({'_id.username': username})]


# =========== ROOM MEMBER METHODS =========== #
def add_room_member(room_id, room_name, username, added_by, is_admin=False):
    room_members_collection.insert_one(
        {'_id': {'room_id': ObjectId(room_id), 'username': username},
         'room_name': room_name,
         'added_by': added_by,
         'added_at': datetime.now(),
         'is_admin': is_admin})


def add_room_members(room_id, room_name, usernames, added_by):
    usernames = list(filter(lambda username: get_user(username) is not None, usernames))
    if len(usernames):
        room_members_collection.insert_many([
            {'_id': {'room_id': ObjectId(room_id), 'username': username},
             'room_name': room_name,
             'added_by': added_by,
             'added_at': datetime.now(),
             'is_admin': False}
            for username in usernames])


def remove_room_members(room_id, usernames):
    room_members_collection\
        .delete_many({'_id': {'$in': [{'room_id': ObjectId(room_id), 'username': username} for username in usernames]}})


def get_room_members(room_id):
    return [member for member in room_members_collection.find({'_id.room_id': ObjectId(room_id)})]


def is_room_member(room_id, username):
    return room_members_collection.count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}})


def is_room_admin(room_id, username):
    return room_members_collection\
        .count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}, 'is_admin': True})


def set_room_admin(room_id, username, new_val):
    room_members_collection.update_one({'_id': {'room_id': ObjectId(room_id), 'username': username}},
                                       {'$set': {'is_admin': new_val}})


# =========== MESSAGE METHODS =========== #
def save_message(room_id, text, sender):
    messages_collection.insert_one({'room_id': room_id, 'text': text, 'sender': sender, 'created_at': datetime.now()})


MESSAGE_FETCH_LIMIT = 6


def get_messages(room_id, page=0):
    offset = page * MESSAGE_FETCH_LIMIT
    messages = [message for message in messages_collection
                .find({'room_id': room_id})
                .sort('_id', DESCENDING)
                .limit(MESSAGE_FETCH_LIMIT)
                .skip(offset)]
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b at %H:%M")
    return messages[::-1]
