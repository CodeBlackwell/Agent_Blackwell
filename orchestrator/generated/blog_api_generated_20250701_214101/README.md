# Simple Blog API

## Project Overview
This project implements a simple blog API that allows users to create, read, update, and delete posts and comments. The API provides endpoints for managing posts and associated comments, enabling basic CRUD operations.

## Setup Instructions
1. Clone the repository
2. Install dependencies with `npm install`
3. Start the server with `npm start`

## API Endpoints
- GET /api/posts: Retrieve all posts
- POST /api/posts: Create a new post
- GET /api/posts/:postId: Retrieve a specific post
- PUT /api/posts/:postId: Update a post
- DELETE /api/posts/:postId: Delete a post
- POST /api/posts/:postId/comments: Add a comment to a post

## Testing
- Run tests with `npm test`