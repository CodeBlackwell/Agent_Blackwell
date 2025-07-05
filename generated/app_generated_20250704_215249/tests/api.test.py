import json
import unittest
from app import app  # Assuming the Flask app is in app.py

class HelloWorldAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_hello_world_endpoint(self):
        """Given the API is running, when the /hello endpoint is accessed,
        then it should return a JSON response with a greeting message."""
        response = self.app.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Hello, World!')

    def test_hello_world_response_format(self):
        """Given the API is running, when the /hello endpoint is accessed,
        then it should return a response in JSON format."""
        response = self.app.get('/hello')
        self.assertEqual(response.content_type, 'application/json')

if __name__ == '__main__':
    unittest.main()