from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

# Define models
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# API Endpoints
class PostResource(Resource):
    def get(self, post_id):
        # Implement GET method
        pass

    def post(self):
        # Implement POST method
        pass

    def put(self, post_id):
        # Implement PUT method
        pass

    def delete(self, post_id):
        # Implement DELETE method
        pass

class CommentResource(Resource):
    def get(self, post_id, comment_id):
        # Implement GET method
        pass

    def post(self, post_id):
        # Implement POST method
        pass

    def put(self, comment_id):
        # Implement PUT method
        pass

    def delete(self, comment_id):
        # Implement DELETE method
        pass

api.add_resource(PostResource, '/posts', '/posts/<int:post_id>')
api.add_resource(CommentResource, '/posts/<int:post_id>/comments', '/comments/<int:comment_id>')

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Simple Blog API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)