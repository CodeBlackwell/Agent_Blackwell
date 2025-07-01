from flask import Flask, request
from flask_restful import Resource, Api
from flask_restplus import fields, Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db = SQLAlchemy(app)
api = Api(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)

db.create_all()

task_model = api.model('Task', {
    'content': fields.String(required=True, description='Task content'),
    'completed': fields.Boolean(description='Task completion status')
})

@api.route('/tasks')
class TaskList(Resource):
    def get(self):
        tasks = Task.query.all()
        return [{'id': task.id, 'content': task.content, 'completed': task.completed} for task in tasks]

    @api.expect(task_model)
    def post(self):
        data = request.json
        new_task = Task(content=data['content'], completed=data.get('completed', False))
        db.session.add(new_task)
        db.session.commit()
        return {'message': 'Task added successfully'}, 201

@api.route('/tasks/<int:task_id>')
class TaskDetail(Resource):
    def delete(self, task_id):
        task = Task.query.get(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
            return {'message': 'Task deleted successfully'}
        return {'message': 'Task not found'}, 404

    def put(self, task_id):
        task = Task.query.get(task_id)
        if task:
            task.completed = True
            db.session.commit()
            return {'message': 'Task marked as complete'}
        return {'message': 'Task not found'}, 404

if __name__ == '__main__':
    app.run(debug=True)