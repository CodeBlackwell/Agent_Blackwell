from flask import Flask
from flask_restplus import Api, Resource

app = Flask(__name__)
api = Api(app)

@api.route('/swagger')
class Swagger(Resource):
    def get(self):
        return api.__schema__

if __name__ == '__main__':
    app.run(debug=True)