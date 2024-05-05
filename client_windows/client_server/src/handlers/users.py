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