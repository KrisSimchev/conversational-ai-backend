import unittest
from flask import Flask, jsonify
from app import app, db
from models import User, GeneratedText

class YourAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_user(self):
        response = self.app.post('/register', json={'username': 'test_user', 'email': 'test@example.com', 'password': 'testpass'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'User registered successfully')
        user = User.query.filter_by(username='test_user').first()
        self.assertIsNotNone(user)

    def test_login_user(self):
        # Assuming the user from the previous test is registered
        response = self.app.post('/login', json={'username': 'test_user', 'password': 'testpass'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Login successful')

    def test_save_text_authenticated(self):
        # First, register a user
        self.app.post('/register', json={'username': 'test_user', 'email': 'test@example.com', 'password': 'testpass'})
        # Login the user
        response_login = self.app.post('/login', json={'username': 'test_user', 'password': 'testpass'})
        token = response_login.get_json()['token']

        # Save text using the authenticated user
        response_save_text = self.app.post('/save_text', json={'thread_id': 'some_thread_id', 'message': 'Hello, World!', 'token': token})
        self.assertEqual(response_save_text.status_code, 200)

        # Check if the text is saved in the database
        generated_text = GeneratedText.query.filter_by(content='Hello, World!').first()
        self.assertIsNotNone(generated_text)
        self.assertEqual(generated_text.user.username, 'test_user')

if __name__ == '__main__':
    unittest.main()