FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . /app

# Environment variables for Neo4j connection (will be overridden by docker-compose)
ENV NEO4J_URI="bolt://localhost:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="password"
ENV NEO4J_DATABASE="neo4j"

EXPOSE 8003

# Command to run the server
CMD ["python", "main.py"]