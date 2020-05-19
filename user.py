from werkzeug.security import check_password_hash

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    # the following four methods are needed by the flask-login library

    # objects of this class will only be instantiated for authenticated users, therefore always true
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    def check_password(self, password_input):  # check if password input matches password via comparing hashes
        return check_password_hash(self.password, password_input)

