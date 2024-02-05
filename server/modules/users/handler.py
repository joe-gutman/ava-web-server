import bcrypt
from datetime import datetime
import utils.exceptions as ex
from utils.logger import logger
from quart import current_app as app

class UserHandler:
    async def register_user(self, data):
        req_keys = ['username', 'password', 'email', 'first_name', 'last_name']
        missing_keys = [key for key in req_keys if key not in data]
        if missing_keys:
            return {'error': f'Missing user information: {", ".join(missing_keys)}'}, 400

        existing_user = await app.db['users'].find_one({'username': data['username'].lower()})
        if existing_user:
            return {'error': 'User already exists'}, 400
        else:
            new_user = {
                'username': data['username'].lower(),
                'password': data['password'],
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': 'user',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'tools': [],
                'message_history': []
            }
            hashed_password = bcrypt.hashpw(new_user['password'].encode('utf-8'), bcrypt.gensalt())
            new_user['password'] = hashed_password
            result = await app.db['users'].insert_one(new_user)
            new_user = await app.db['users'].find_one({'_id': result.inserted_id}, {'password': 0, 'tools': 0, 'message_history': 0})
            logger.info(f"User {new_user['username']} registered")
            return {'status': 'success', 'message': f"User {new_user['username']} registered", 'user': {**new_user, '_id': str(new_user['_id'])}}, 201

    async def login_user(self, data):
        if 'username' not in data or 'password' not in data:
            return {'status': 'bad request', 'message': 'Missing username or password'}, 400

        user = await app.db['users'].find_one({'username': data['username'].lower()})
        if not user:
            return {'status': 'error', 'message': 'Incorrect username or password'}, 401

        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            return {'status': 'error', 'message': 'Incorrect username or password'}, 401

        user.pop('password')
        logger.info(f"User {user['username']} logged in")
        return {'status': 'success', 'message': f"User {user['username']} logged in", 'user': {**user, '_id': str(user['_id'])}}, 200