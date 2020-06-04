# Python-Chat-App
Simple chat app built with Python using MongoDB, Flask and SocketIO.

## Functionality
The app fulfils all the necessary functionality of a chat app. This entails:
1. User registration and login
2. Creating, managing and deleting chatrooms
3. The actual chat mechanic, with chat history

### Users
A user account is created with an email address, password and **unique username** - users will be informed about
conflicting usernames. A user can log into his account in order to access the chat app. The session persists
for an amount of time or until the user logs out. Closing the browser tab or window **does not terminate the session**.

---
### Chatrooms
Upon login, the user sees a list of chatrooms which he is a member of. The user may join any of these and participate
in the chat. A logged in user can be added to chatrooms or create his own. When added to a chatroom, a user becomes a
regular member by default. When creating a chatroom, the user becomes an administrator. In order to create a room,
the user must provide a name for it.

All administrators of a room are **equal in power** and can:
- change the room name
- edit the list of members of a room
- grant and revoke admin privileges from all users, **including each other**
- delete the chat room

A regular user may leave a chatroom at any time. An administrator needs to **relinquish that role before leaving**. An
administrator can only relinquish their role if there are other administrators present. If that is not the case,
**another administrator must first be appointed**.

---
### Chat
Every message sent to a chatroom **is visible to all its members**. Messages cannot be deleted or modified once sent.
Every message comes equipped with a timestamp and the username of its sender. This information is stored in that
chatroom's message history.

Upon entering a chatroom, a set amount of past messages is loaded from history. A user may load further past messages.
No set limit exists, **all users can access the entire message history**.

The chatroom is notified of members entering and leaving. Leaving the chat is synonymous with navigating away from it,
which includes entering the chatroom management tab.
