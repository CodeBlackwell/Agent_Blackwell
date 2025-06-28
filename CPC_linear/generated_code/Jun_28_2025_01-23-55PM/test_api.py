import requests

# Test GET /todos
response = requests.get('http://localhost:5000/todos')
print(response.json())

# Test POST /todos
new_todo = {'task': 'Complete assignment', 'completed': False}
response = requests.post('http://localhost:5000/todos', json=new_todo)
print(response.json())

# Test PUT /todos/:id
updated_todo = {'task': 'Complete assignment', 'completed': True}
response = requests.put('http://localhost:5000/todos/0', json=updated_todo)
print(response.json())

# Test DELETE /todos/:id
response = requests.delete('http://localhost:5000/todos/0')
print(response.json())