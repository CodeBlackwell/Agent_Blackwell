from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/user')
def get_user_info():
    # Connect to the database and write a query to retrieve user information
    user_info = {'name': 'John Doe', 'email': 'john.doe@example.com'}
    return jsonify(user_info)

if __name__ == '__main__':
    app.run()