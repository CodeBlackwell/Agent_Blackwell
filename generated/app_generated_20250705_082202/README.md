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

3. Run the application:
   ```bash
   npm start
   ```

4. Test the API:
   Use Postman or a similar tool to send a GET request to `http://localhost:3000/hello`.

## API Documentation

- **Endpoint**: `GET /hello`
- **Response Format**: JSON
- **Response Example**:
  ```json
  {
    "message": "Hello World"
  }
  ```