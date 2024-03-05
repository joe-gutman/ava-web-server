# file for custom exceptions
# error code for db authentication error

class DBAUTHERROR(Exception):
    def __init__(self, message="Error with db authentication. Please check your environment configuration"):
        self.message = message
        super().__init__(self.message)

class DBCONNECTIONERROR(Exception):
    def __init__(self, message="Error connecting to db"):
        self.message = message
        super().__init__(self.message)

class MissingCredentialsError(Exception):
    def __init__(self, message="Missing username or password"):
        self.message = message
        super().__init__(self.message)

class UserAlreadyExistsError(Exception):
    def __init__(self, message="User already exists"):
        self.message = message
        super().__init__(self.message)

class DBRegistrationError(Exception):
    def __init__(self, message="Error registering user in database"):
        self.message = message
        super().__init__(self.message)

class LoginError(Exception):
    def __init__(self, message="Incorrect username or password"):
        self.message = message
        super().__init__(self.message)

class DBLoginError(Exception):
    def __init__(self, message="Error logging in user"):
        self.message = message
        super().__init__(self.message)

class UserNotFoundError(Exception):
    def __init__(self, message="Cannot find user in database"):
        self.message = message
        super().__init__(self.message)