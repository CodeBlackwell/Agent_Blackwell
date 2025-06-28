import unittest
from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_hello_world(self):
        response = self.app.get('/')
        self.assertEqual(response.data.decode('utf-8'), 'Hello, World!')

    def test_get_user(self):
        response = self.app.get('/user/123')
        self.assertEqual(response.data.decode('utf-8'), 'Retrieving information for user 123')

if __name__ == '__main__':
    unittest.main()