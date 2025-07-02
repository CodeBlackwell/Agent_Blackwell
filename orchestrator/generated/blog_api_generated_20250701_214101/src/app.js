const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

// MongoDB connection
mongoose.connect('mongodb://localhost/simple-blog-api', { useNewUrlParser: true, useUnifiedTopology: true });
const db = mongoose.connection;
db.on('error', console.error.bind(console, 'MongoDB connection error:'));

// Define Post and Comment schemas
const postSchema = new mongoose.Schema({
  title: String,
  content: String,
  author: String,
  comments: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Comment' }]
});

const commentSchema = new mongoose.Schema({
  text: String,
  author: String
});

const Post = mongoose.model('Post', postSchema);
const Comment = mongoose.model('Comment', commentSchema);

// API endpoints
// Implement API endpoints for posts and comments here

app.listen(3000, () => {
  console.log('Server is running on http://localhost:3000');
});

module.exports = app;