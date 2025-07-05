# Hello World API

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hello-world-api
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the server:
   ```bash
   npm start
   ```

4. Test the API endpoint:
   - Open Postman or a similar tool.
   - Send a GET request to `http://localhost:3000/hello`.
   - You should receive a JSON response:
     ```json
     {
       "message": "Hello, World!"
     }
     ```