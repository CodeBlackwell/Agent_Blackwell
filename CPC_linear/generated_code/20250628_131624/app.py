from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/user/<user_id>')
def get_user(user_id):
    # Logic to retrieve user information from the database
    return f'Retrieving information for user {user_id}'

if __name__ == '__main__':
    app.run()