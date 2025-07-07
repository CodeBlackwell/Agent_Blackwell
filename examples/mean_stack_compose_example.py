"""
Example: MEAN Stack Application with Docker Compose Support

This example demonstrates how the MVP Incremental Workflow can generate
and validate a complete MEAN stack application using multi-container orchestration.
"""

# Example requirements for a MEAN stack application
MEAN_STACK_REQUIREMENTS = """
Create a MEAN stack task management application with the following requirements:

1. **MongoDB Database**:
   - Store tasks with title, description, status, and timestamps
   - Use MongoDB 5.0 or later
   - Configure with authentication

2. **Express.js Backend API**:
   - RESTful API with CRUD operations for tasks
   - Connect to MongoDB using Mongoose
   - CORS enabled for frontend access
   - Environment-based configuration
   - Health check endpoint at /api/health

3. **Angular Frontend**:
   - Task list view with add/edit/delete functionality
   - Responsive design using Angular Material
   - Connect to backend API
   - Production-ready build

4. **Docker Compose Setup**:
   - Three services: mongodb, api, frontend
   - Proper networking between services
   - Environment variables for configuration
   - Health checks for all services
   - Volume persistence for MongoDB

5. **Project Structure**:
   ```
   backend/
     ├── src/
     │   ├── models/
     │   │   └── task.model.js
     │   ├── routes/
     │   │   └── task.routes.js
     │   ├── config/
     │   │   └── database.js
     │   └── server.js
     ├── package.json
     └── Dockerfile
   
   frontend/
     ├── src/
     │   ├── app/
     │   │   ├── components/
     │   │   ├── services/
     │   │   └── models/
     │   └── environments/
     ├── package.json
     ├── angular.json
     └── Dockerfile
   
   docker-compose.yml
   .env.example
   README.md
   ```

6. **Testing Requirements**:
   - Backend API tests using Jest
   - Frontend unit tests using Karma/Jasmine
   - Integration tests to verify service connectivity

Generate the complete application with all files needed to run the MEAN stack.
"""

# Example of expected docker-compose.yml output
EXPECTED_COMPOSE_OUTPUT = """
version: '3.8'

services:
  mongodb:
    image: mongo:5
    container_name: mean_mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-password}
      MONGO_INITDB_DATABASE: ${MONGO_DB:-taskmanager}
    volumes:
      - mongodb_data:/data/db
    networks:
      - backend
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  api:
    build: ./backend
    container_name: mean_api
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: ${NODE_ENV:-development}
      PORT: 3000
      MONGO_URI: mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-password}@mongodb:27017/${MONGO_DB:-taskmanager}?authSource=admin
      JWT_SECRET: ${JWT_SECRET:-your-secret-key}
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build: ./frontend
    container_name: mean_frontend
    ports:
      - "4200:80"
    environment:
      API_URL: http://api:3000
    depends_on:
      api:
        condition: service_healthy
    networks:
      - frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

volumes:
  mongodb_data:
    driver: local
"""

# How to use with the workflow
def demo_mean_stack_workflow():
    """
    Example of using the MVP Incremental Workflow with MEAN stack requirements
    """
    from orchestrator.orchestrator_agent import run_enhanced_coding_workflow
    from shared.data_models import CodingTeamInput
    
    # Create input
    team_input = CodingTeamInput(
        requirements=MEAN_STACK_REQUIREMENTS,
        workflow_type="mvp_incremental"
    )
    
    # Run workflow
    print("🚀 Starting MEAN Stack Generation...")
    results = run_enhanced_coding_workflow(team_input)
    
    # The workflow will:
    # 1. Plan the MEAN stack architecture
    # 2. Design the component structure
    # 3. Implement features incrementally:
    #    - MongoDB setup and models
    #    - Express API implementation
    #    - Angular frontend
    #    - Docker configuration
    # 4. Validate using multi-container orchestration
    # 5. Run integration tests
    
    print("\n✅ MEAN Stack application generated successfully!")
    print("\nTo run the application:")
    print("1. cd to the generated directory")
    print("2. Copy .env.example to .env and configure")
    print("3. Run: docker-compose up -d")
    print("4. Access frontend at http://localhost:4200")
    print("5. Access API at http://localhost:3000")


# Test commands that will be run during validation
VALIDATION_TEST_COMMANDS = [
    # API health check
    "curl -f http://localhost:3000/api/health",
    
    # Database connectivity test
    "curl -X GET http://localhost:3000/api/tasks",
    
    # Frontend accessibility
    "curl -f http://localhost:80",
    
    # Create a test task
    'curl -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d \'{"title":"Test Task","description":"Test Description"}\'',
]

if __name__ == "__main__":
    # This is just an example - actual usage would be through the workflow
    print("MEAN Stack Compose Example")
    print("=" * 50)
    print("\nRequirements:")
    print(MEAN_STACK_REQUIREMENTS)
    print("\nExpected docker-compose.yml:")
    print(EXPECTED_COMPOSE_OUTPUT)
    print("\nValidation commands:")
    for cmd in VALIDATION_TEST_COMMANDS:
        print(f"  - {cmd}")
"""