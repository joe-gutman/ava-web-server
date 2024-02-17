import aiohttp
import json
from utils.logger import logger


class User:
    def __init__(self, user_data):
        self.id = user_data['_id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.role = user_data['role']
        self.created_at = user_data['created_at']
        self.message_history = user_data['message_history']

    def __str__(self):
        return f'User: {self.username}'
    
    @classmethod
    async def login(cls, username, password):
        data = {
            'username': username,
            'password': password
        }
        logger.info('Logging in...')
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:5000/user/login', json=data) as response:
                response = json.loads(await response.text())
                logger.debug(response)
                if response['status'] == 'success':
                    user = cls(response['user'])
                    logger.info(f"Login successful with user: {user.username}")
                    logger.info(f"Login message: {response['message']}")
                    return user
                else:
                    logger.error(f"Login failed with status: {response['status']}")
                    logger.error(f"Login message: {response['message']}")
                    return None