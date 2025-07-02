const chai = require('chai');
const chaiHttp = require('chai-http');
const app = require('../src/app');

chai.use(chaiHttp);
const expect = chai.expect;

describe('Blog API', () => {
  it('should return all posts', (done) => {
    chai.request(app)
      .get('/api/posts')
      .end((err, res) => {
        expect(res).to.have.status(200);
        expect(res.body).to.be.an('array');
        done();
      });
  });

  // Add more test cases for other endpoints
});