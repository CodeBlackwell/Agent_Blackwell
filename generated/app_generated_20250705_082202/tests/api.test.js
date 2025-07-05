const request = require('supertest');
const app = require('../src/server');

describe('Hello World API', () => {
    test('GET /hello returns a JSON response with "Hello World"', async () => {
        const response = await request(app).get('/hello');
        expect(response.status).toBe(200);
        expect(response.body).toEqual({ message: 'Hello World' });
        expect(response.headers['content-type']).toMatch(/json/);
    });

    test('GET /hello is stateless and returns the same response on multiple requests', async () => {
        const response1 = await request(app).get('/hello');
        const response2 = await request(app).get('/hello');
        expect(response1.body).toEqual(response2.body);
    });
});