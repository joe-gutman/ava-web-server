import bcrypt
import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from app.users.handler import User, UserHandler
from app.utils.logger import get_logger

logger = get_logger(__name__, "DEBUG")

class TestUserHandler(unittest.TestCase):
    @patch('pymongo.collection.Collection.insert_one', new_callable=AsyncMock)
    @patch('pymongo.collection.Collection.find_one', new_callable=AsyncMock)
    def test_register_user(self, mock_insert_one, mock_find_one):
        # Arrange
        mock_db = MagicMock()
        mock_db['users'].insert_one = mock_insert_one
        mock_db['users'].find_one = mock_find_one

        user_handler = UserHandler(mock_db)
        data = {'username': 'test', 'password': 'password'}
        mock_insert_one.return_value = AsyncMock(inserted_id="some_id")
        mock_find_one.return_value = data

        # Act
        response, status_code = asyncio.run(user_handler.register_user(data))

        # Assert
        self.assertEqual(status_code, 201)
        self.assertEqual(response['success'], 'User registered')
        self.assertIn('user', response)

    # TODO: Add a test for the login_user method     
    @patch('pymongo.collection.Collection.find_one', new_callable=AsyncMock)
    def test_login_user(self, mock_find_one):
        # Arrange
        mock_db = MagicMock()
        mock_db['users'].find_one = mock_find_one

        user_handler = UserHandler(mock_db)
        data = {'username': 'test', 'password': 'password'}
        mock_find_one.return_value = data

        # Act
        response, status_code = asyncio.run(user_handler.login_user(data))

        # Assert
        self.assertEqual(status_code, 200)
        self.assertEqual(response['success'], f"User {data['username']} logged in")
        self.assertIn('user', response)

if __name__ == '__main__':
    unittest.main()