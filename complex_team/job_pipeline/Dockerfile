FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv for virtual environment and dependency management
RUN pip install uv

# Create a virtual environment
RUN uv venv /app/.venv

# Install dotenv for environment variable management
RUN uv pip install python-dotenv

# Copy the entire application first
COPY . .

# Install dependencies using uv (without touching the global environment)
RUN uv pip install -e .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Create empty .env file if it doesn't exist to prevent errors
RUN touch .env

# Default command to keep container running
CMD ["sh", "-c", "echo 'Container is running. Use docker-compose commands to interact with services.'"]
