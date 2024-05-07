import bcrypt
from datetime import datetime
from utils.logger import logger
from quart import current_app as app

class UserHandler:
    @staticmethod
    async def register_user(request):
        try: 
            req_keys = ['username', 'password', 'email', 'first_name', 'last_name']
            missing_keys = [key for key in req_keys if key not in data]
            if missing_keys:
                return {'error': f'Missing user information: {", ".join(missing_keys)}'}, 400

            existing_user = await app.db['users'].find_one({'username': data['username'].lower()})
            if existing_user:
                return {
                    'status': 'error',
                    'message': 'User already exists'
                }, 400
            else:
                new_user = to_lowercase(request['data']['content'])
                new_user['password'] = bcrypt.hashpw(request['data']['content']['password'].encode('utf-8'), bcrypt.gensalt())
                result = await app.db['users'].insert_one(new_user)

                new_user = await app.db['users'].find_one({'_id': result.inserted_id}, {'password': 0})
                logger.info(f"User {new_user['username']} registered")

                return {
                    'status': 'success', 
                    'message': f"User {new_user['username']} registered", 
                    'user': { **new_user, '_id': str(new_user['_id'])}
                    }, 201
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {
                'status': 'error', 
                'message': 'Error registering user'
            }, 500

    @staticmethod
    async def login_user(data):
        if 'username' not in data or 'password' not in data:
            return {
                'status': 'error', 
                'message': 'Missing username or password'
            }, 400

        user = await app.db['users'].find_one({'username': data['username'].lower()})
        if not user:
            return {
                'status': 'error', 
                'message': 'Incorrect username or password'
            }, 401

        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            return {
                'status': 'error', 
                'message': 'Incorrect username or password'
            }, 401

        user.pop('password')
        logger.info(f"User {user['username']} logged in")
        return {
            'status': 'success', 
            'message': f"User {user['username']} logged in", 
            'user': {**user, '_id': str(user['_id'])}
        }, 200