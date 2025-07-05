const request = require('supertest');
const app = require('../src/app');

describe('Hello World API', () => {
  test('GET /hello returns Hello World message', async () => {
    const response = await request(app).get('/hello');
    expect(response.status).toBe(200);
    expect(response.headers['content-type']).toEqual(expect.stringContaining("json"));
    expect(response.body).toEqual({ message: "Hello, World!" });
  });

  test('API documentation is present', async () => {
    const fs = require('fs').promises;
    const readme = await fs.readFile('README.md', 'utf8');
    expect(readme).toMatch(/How to run the API/);
    expect(readme).toMatch(/How to test the API/);
  });
});