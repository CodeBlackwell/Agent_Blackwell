const request = require('supertest');
const app = require('../src/server');

describe('Hello World API', () => {
  it('should return a JSON response with the message "Hello, World!"', async () => {
    const response = await request(app).get('/hello');
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ message: 'Hello, World!' });
    expect(response.headers['content-type']).toEqual(expect.stringContaining('json'));
  });

  it('should return response in JSON format', async () => {
    const response = await request(app).get('/hello');
    expect(response.headers['content-type']).toEqual(expect.stringContaining('json'));
  });
});