FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies including OpenSSL and curl for health checks
RUN apt-get update && apt-get install -y \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for authentication config, SSL certificates, MCP servers, and wheat data
RUN mkdir -p keys ssl mcp_servers/company_tagging/categories wheat_pages wheat_helpers mcp_pages

# Copy the application code
COPY . .

# Copy wheat-specific files
COPY pages/ ./pages/
COPY wheat_helpers/ ./wheat_helpers/
COPY database_setup/ ./database_setup/
COPY wheat_production.db ./wheat_production.db



# Copy SSL-related scripts and make them executable
COPY generate_ssl_certificate.sh startup_ssl.sh ./
RUN chmod +x generate_ssl_certificate.sh startup_ssl.sh

# Ensure proper permissions for directories
RUN chmod 755 keys ssl mcp_servers wheat_pages wheat_helpers mcp_pages

# Initialize the wheat database if it doesn't exist
# RUN if [ ! -f wheat_production.db ]; then \
#         cd database_setup && \
#         python database_setup.py && \
#         python database_setup_exports.py && \
#         python database_setup_imports.py && \
#         python database_setup_stocks.py && \
#         python database_setup_su_ratio.py && \
#         python database_setup_acreage.py && \
#         python database_setup_yield.py && \
#         cd ..; \
#     fi

# Expose both HTTP and HTTPS ports
EXPOSE 8501
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501 || exit 1

# Run as root to avoid SSL permission issues
CMD ["./startup_ssl.sh"]