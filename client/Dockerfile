FROM python:3.11-slim-bullseye

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create keys directory for authentication config
RUN mkdir -p keys

# Copy the application code
COPY . .

# Ensure proper permissions for keys directory
RUN chmod 755 keys

# Expose the port
EXPOSE 8501

# Default command - will be overridden by docker-compose
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]