from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from user import User

# USER:        _id, email, password (hashed)
# ROOM:        _id, room_name, created_by, created_at
# ROOM MEMBER: _id: {room_id, username}, room_name, added_by, added_at, is_admin


client = MongoClient("mongodb+srv://FluffyNinjaBrick:Marcjanin123@dblab-lnoyu.mongodb.net/test?retryWrites=true&w=majority")

chat_db = client.get_database('ChatDB')
users_collection = chat_db.get_collection("users")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")


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


def get_rooms_for_user(username):
    rooms = []
    for room in room_members_collection.find({'_id.username': username}):
        rooms.append(room)
    return rooms


# =========== ROOM MEMBER METHODS =========== #
def add_room_member(room_id, room_name, username, added_by, is_admin=False):
    room_members_collection.insert_one(
        {'_id': {'room_id': ObjectId(room_id), 'username': username},
         'room_name': room_name,
         'added_by': added_by,
         'added_at': datetime.now(),
         'is_admin': is_admin})


def add_room_members(room_id, room_name, usernames, added_by):
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
    members = []
    for member in room_members_collection.find({'_id.room_id': ObjectId(room_id)}):
        members.append(member)
    return members


def is_room_member(room_id, username):
    return room_members_collection.count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}})


def is_room_admin(room_id, username):
    return room_members_collection\
        .count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}, 'is_admin': True})
