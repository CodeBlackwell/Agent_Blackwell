const request = require('supertest');
const app = require('../src/app');
const Todo = require('../src/models/todo');

describe('Todo API', () => {
  beforeAll(async () => {
    await Todo.deleteMany({});
  });

  it('GET /todos - List all todos', async () => {
    const res = await request(app).get('/todos');
    expect(res.statusCode).toEqual(200);
    expect(Array.isArray(res.body)).toBeTruthy();
  });

  it('POST /todos - Create a new todo', async () => {
    const res = await request(app).post('/todos').send({ title: 'Test Todo' });
    expect(res.statusCode).toEqual(201);
    expect(res.body.title).toEqual('Test Todo');
  });

  it('GET /todos/:id - Get a specific todo', async () => {
    const todo = await Todo.create({ title: 'Test Todo' });
    const res = await request(app).get(`/todos/${todo._id}`);
    expect(res.statusCode).toEqual(200);
    expect(res.body.title).toEqual('Test Todo');
  });

  it('PUT /todos/:id - Update a todo', async () => {
    const todo = await Todo.create({ title: 'Test Todo' });
    const res = await request(app).put(`/todos/${todo._id}`).send({ title: 'Updated Todo' });
    expect(res.statusCode).toEqual(200);
    expect(res.body.title).toEqual('Updated Todo');
  });

  it('DELETE /todos/:id - Delete a todo', async () => {
    const todo = await Todo.create({ title: 'Test Todo' });
    const res = await request(app).delete(`/todos/${todo._id}`);
    expect(res.statusCode).toEqual(200);
    expect(res.text).toEqual('Todo deleted');
  });
});