FROM python:3.11-slim-bullseye

WORKDIR /app

# Install OpenSSL and dos2unix for certificate generation and line ending fixes
RUN apt-get update && apt-get install -y openssl dos2unix && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for authentication config and SSL certificates
RUN mkdir -p keys ssl

# Copy the application code
COPY . .

# Fix line endings for all shell scripts (more comprehensive)
RUN find . -name "*.sh" -type f -exec dos2unix {} \;

# Make all shell scripts executable
RUN find . -name "*.sh" -type f -exec chmod +x {} \;

# Ensure proper permissions for directories
RUN chmod 755 keys ssl

# Expose both HTTP and HTTPS ports
EXPOSE 8501
EXPOSE 8502

# Use the startup script as default command
CMD ["/app/startup_ssl.sh"]