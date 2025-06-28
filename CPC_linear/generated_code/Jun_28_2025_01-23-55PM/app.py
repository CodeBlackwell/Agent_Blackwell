from flask import Flask, request, jsonify

app = Flask(__name__)

todos = []

@app.route('/todos', methods=['GET'])
def get_todos():
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    todos.append(data)
    return jsonify(data), 201

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    data = request.get_json()
    todos[id] = data
    return jsonify(data)

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    deleted_todo = todos.pop(id)
    return jsonify(deleted_todo)

if __name__ == '__main__':
    app.run()