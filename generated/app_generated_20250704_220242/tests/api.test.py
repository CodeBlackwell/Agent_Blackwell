import json
import unittest
from app import app  # Assuming the Flask app is in app.py

class HelloWorldAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_hello_world_endpoint(self):
        """Given the API is running, when a GET request is made to /hello, 
        then it should return a JSON response with the message 'Hello, World!'."""
        response = self.app.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(json.loads(response.data), {"message": "Hello, World!"})

    def test_hello_world_response_structure(self):
        """Given the API is running, when a GET request is made to /hello, 
        then the response should have the correct structure."""
        response = self.app.get('/hello')
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], "Hello, World!")

if __name__ == '__main__':
    unittest.main()