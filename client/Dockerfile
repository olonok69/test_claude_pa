FROM python:3.11-slim-bullseye

WORKDIR /app

# Install OpenSSL for certificate generation
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for authentication config and SSL certificates
RUN mkdir -p keys ssl

# Copy the application code
COPY . .

# Copy SSL-related scripts and fix line endings
COPY generate_ssl_certificate.sh startup_ssl.sh ./
RUN sed -i 's/\r$//' startup_ssl.sh generate_ssl_certificate.sh

RUN chmod +x /app/generate_ssl_certificate.sh /app/startup_ssl.sh
RUN chmod 777 /app/startup_ssl.sh
# Ensure proper permissions for directories
RUN chmod 755 keys ssl

# Expose both HTTP and HTTPS ports
EXPOSE 8501
EXPOSE 8502

# Use the startup script as default command
CMD ["/app/startup_ssl.sh"]
#ENTRYPOINT ["/bin/sh"]
