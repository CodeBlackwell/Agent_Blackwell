from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

# Define Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)

# Define Task Schema
class TaskSchema(ma.Schema):
    class Meta:
        fields = ('id', 'content', 'completed')

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

# Routes for add, delete, and mark complete operations
class TaskResource(Resource):
    def post(self):
        content = request.json['content']
        new_task = Task(content=content)
        db.session.add(new_task)
        db.session.commit()
        return task_schema.jsonify(new_task)

    def delete(self, task_id):
        task = Task.query.get(task_id)
        db.session.delete(task)
        db.session.commit()
        return task_schema.jsonify(task)

    def put(self, task_id):
        task = Task.query.get(task_id)
        task.completed = True
        db.session.commit()
        return task_schema.jsonify(task)

api.add_resource(TaskResource, '/tasks', '/tasks/<int:task_id>')

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Simple Todo List API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)