const express = require('express');
const router = express.Router();
const Todo = require('../models/todo');
const Joi = require('joi');

// Validation schema
const todoSchema = Joi.object({
  title: Joi.string().required(),
  description: Joi.string(),
  completed: Joi.boolean()
});

// GET /todos
router.get('/', async (req, res) => {
  const todos = await Todo.find();
  res.json(todos);
});

// POST /todos
router.post('/', async (req, res) => {
  const { error } = todoSchema.validate(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const todo = new Todo(req.body);
  await todo.save();
  res.status(201).json(todo);
});

// GET /todos/:id
router.get('/:id', async (req, res) => {
  const todo = await Todo.findById(req.params.id);
  if (!todo) return res.status(404).send('Todo not found');
  res.json(todo);
});

// PUT /todos/:id
router.put('/:id', async (req, res) => {
  const { error } = todoSchema.validate(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const todo = await Todo.findByIdAndUpdate(req.params.id, req.body, { new: true });
  if (!todo) return res.status(404).send('Todo not found');
  res.json(todo);
});

// DELETE /todos/:id
router.delete('/:id', async (req, res) => {
  const todo = await Todo.findByIdAndDelete(req.params.id);
  if (!todo) return res.status(404).send('Todo not found');
  res.send('Todo deleted');
});

module.exports = router;