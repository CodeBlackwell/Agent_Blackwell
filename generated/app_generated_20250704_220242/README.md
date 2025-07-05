# Hello World REST API

## Setup Instructions

1. **Install Python**: Make sure you have Python installed on your machine.
2. **Install Dependencies**: Run the following command to install Flask:
   ```
   pip install -r requirements.txt
   ```
3. **Run the API**: Start the Flask application by running:
   ```
   python app.py
   ```
4. **Test the API**: Use Postman or a similar tool to send a GET request to:
   ```
   http://127.0.0.1:5000/hello
   ```
   You should receive a JSON response:
   ```json
   {
     "message": "Hello, World!"
   }
   ```

## Running Tests

To run the tests, execute the following command: