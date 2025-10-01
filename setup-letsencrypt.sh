#!/bin/bash

# ============================================
# Complete Let's Encrypt Setup Script
# For: data.forensic-bot.com
# ============================================

set -e  # Exit on error

# Configuration
DOMAIN="data.forensic-bot.com"
EMAIL="olonok@gmail.com"
RSA_KEY_SIZE=4096
DATA_PATH="./certbot"
STAGING=0  # Set to 1 for testing (to avoid rate limits)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Let's Encrypt Setup for $DOMAIN${NC}"
echo -e "${GREEN}Email: $EMAIL${NC}"
echo -e "${GREEN}============================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command_exists docker; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command_exists docker compose || ! docker compose version >/dev/null 2>&1; then
    if ! command_exists docker-compose; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    # Use docker-compose if docker compose doesn't work
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Step 1: Stop existing containers
echo -e "${YELLOW}Step 1: Stopping existing containers...${NC}"
$COMPOSE_CMD down || true

# Step 2: Create required directories
echo -e "${YELLOW}Step 2: Creating required directories...${NC}"
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"
mkdir -p nginx/conf.d
mkdir -p logs/nginx

# Step 3: Download recommended TLS parameters
echo -e "${YELLOW}Step 3: Downloading recommended TLS parameters...${NC}"
if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ] || [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    echo "Downloading TLS configuration files..."
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
    echo -e "${GREEN}TLS parameters downloaded successfully${NC}"
fi

# Step 4: Create nginx configuration for Let's Encrypt
echo -e "${YELLOW}Step 4: Creating Nginx configuration...${NC}"
cat > nginx/conf.d/default.conf << 'EOF'
# HTTP server - for Let's Encrypt challenge and redirect
server {
    listen 80;
    listen [::]:80;
    server_name data.forensic-bot.com;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name data.forensic-bot.com;

    # SSL certificates from Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    # Include Let's Encrypt recommended settings
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Additional security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Root directory
    root /usr/share/nginx/html;
    index index.html;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }

    # SSE endpoint - HTTP backend
    location /sse {
        proxy_pass http://mcp-server-http:8008/sse;
        proxy_http_version 1.1;
        
        # SSE specific headers
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        
        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        
        # Response headers for SSE
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
        add_header X-Accel-Buffering no;
    }

    # SSE endpoint - HTTPS backend
    location /secure-sse {
        proxy_pass https://mcp-server-https:8443/sse;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        
        # SSE specific headers
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        
        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        
        # Response headers for SSE
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
        add_header X-Accel-Buffering no;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://mcp-server-http:8008/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Step 5: Create/Update docker-compose.yml for production
echo -e "${YELLOW}Step 5: Creating production docker-compose configuration...${NC}"
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # HTTP SSE server
  mcp-server-http:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: mcp-server-http
    expose:
      - "8008"
    environment:
      - MSSQL_HOST=${MSSQL_HOST}
      - MSSQL_USER=${MSSQL_USER}
      - MSSQL_PASSWORD=${MSSQL_PASSWORD}
      - MSSQL_DATABASE=${MSSQL_DATABASE}
      - MSSQL_DRIVER=ODBC Driver 18 for SQL Server
      - TrustServerCertificate=yes
      - Trusted_Connection=no
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mcp-network
    restart: unless-stopped

  # HTTPS SSE server
  mcp-server-https:
    build: 
      context: .
      dockerfile: Dockerfile.https
    container_name: mcp-server-https
    expose:
      - "8443"
    environment:
      - MSSQL_HOST=${MSSQL_HOST}
      - MSSQL_USER=${MSSQL_USER}
      - MSSQL_PASSWORD=${MSSQL_PASSWORD}
      - MSSQL_DATABASE=${MSSQL_DATABASE}
      - USE_HTTPS=${USE_HTTPS}
      - MSSQL_DRIVER=ODBC Driver 18 for SQL Server
      - TrustServerCertificate=yes
      - Trusted_Connection=no
      - SSL_CERT_PATH=/app/certs/server.crt
      - SSL_KEY_PATH=/app/certs/server.key
    healthcheck:
      test: ["CMD", "curl", "-k", "-f", "https://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mcp-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nginx-forensic-bot
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./app:/usr/share/nginx/html:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - mcp-server-http
      - mcp-server-https
    networks:
      - mcp-network
    restart: unless-stopped
    command: "/bin/sh -c 'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot
    container_name: certbot-forensic-bot
    volumes:
      - ./certbot/conf:/etc/letsencrypt:rw
      - ./certbot/www:/var/www/certbot:rw
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - mcp-network
    restart: unless-stopped

networks:
  mcp-network:
    driver: bridge

volumes:
  nginx_logs:
    driver: local
EOF

# Step 6: Check if certificates already exist
echo -e "${YELLOW}Step 6: Checking for existing certificates...${NC}"
if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
    echo -e "${YELLOW}Existing certificate found for $DOMAIN${NC}"
    read -p "Do you want to replace the existing certificate? (y/N) " decision
    if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
        echo -e "${GREEN}Keeping existing certificate. Starting services...${NC}"
        $COMPOSE_CMD -f docker-compose.prod.yml up -d
        exit 0
    fi
fi

# Step 7: Create dummy certificate for nginx to start
echo -e "${YELLOW}Step 7: Creating dummy certificate...${NC}"
path="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "$DATA_PATH/conf/live/$DOMAIN"
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    --entrypoint "openssl" \
    certbot/certbot \
    req -x509 -nodes -newkey rsa:1024 -days 1 \
    -keyout "$path/privkey.pem" \
    -out "$path/fullchain.pem" \
    -subj "/CN=localhost"

# Step 8: Start nginx with dummy certificate
echo -e "${YELLOW}Step 8: Starting nginx...${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
echo "Waiting for nginx to start..."
sleep 5

# Step 9: Delete dummy certificate
echo -e "${YELLOW}Step 9: Removing dummy certificate...${NC}"
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    --entrypoint "rm" \
    certbot/certbot \
    -rf "/etc/letsencrypt/live/$DOMAIN" \
    "/etc/letsencrypt/archive/$DOMAIN" \
    "/etc/letsencrypt/renewal/$DOMAIN.conf"

# Step 10: Request Let's Encrypt certificate
echo -e "${YELLOW}Step 10: Requesting Let's Encrypt certificate...${NC}"

# Select staging or production
if [ $STAGING != "0" ]; then 
    STAGING_ARG="--staging"
    echo -e "${YELLOW}Using Let's Encrypt STAGING environment (for testing)${NC}"
else
    STAGING_ARG=""
    echo -e "${GREEN}Using Let's Encrypt PRODUCTION environment${NC}"
fi

docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot \
    certonly --webroot \
    -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    -d $DOMAIN \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal

# Check if certificate was obtained successfully
if [ ! -f "$DATA_PATH/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}Failed to obtain certificate!${NC}"
    echo -e "${RED}Please check the error messages above.${NC}"
    exit 1
fi

# Step 11: Reload nginx with new certificate
echo -e "${YELLOW}Step 11: Reloading nginx with new certificate...${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml exec nginx nginx -s reload

# Step 12: Start all services including certbot for auto-renewal
echo -e "${YELLOW}Step 12: Starting all services with auto-renewal...${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml up -d

# Step 13: Test the setup
echo -e "${YELLOW}Step 13: Testing the setup...${NC}"
sleep 5

# Test HTTP redirect
echo -e "${YELLOW}Testing HTTP to HTTPS redirect...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I http://$DOMAIN)
if [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✓ HTTP redirect working${NC}"
else
    echo -e "${YELLOW}⚠ HTTP redirect returned status: $HTTP_STATUS${NC}"
fi

# Test HTTPS
echo -e "${YELLOW}Testing HTTPS connection...${NC}"
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health)
if [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ HTTPS working with valid certificate${NC}"
else
    echo -e "${YELLOW}⚠ HTTPS returned status: $HTTPS_STATUS${NC}"
fi

# Show certificate information
echo -e "${YELLOW}Certificate information:${NC}"
echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates

# Final status
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${GREEN}Your services are now available at:${NC}"
echo -e "  • Health check: ${GREEN}https://$DOMAIN/health${NC}"
echo -e "  • SSE endpoint: ${GREEN}https://$DOMAIN/sse${NC}"
echo -e "  • Secure SSE:   ${GREEN}https://$DOMAIN/secure-sse${NC}"
echo ""
echo -e "${GREEN}Certificate auto-renewal is configured and will run twice daily.${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  • View logs:        ${YELLOW}$COMPOSE_CMD -f docker-compose.prod.yml logs -f${NC}"
echo -e "  • Restart services: ${YELLOW}$COMPOSE_CMD -f docker-compose.prod.yml restart${NC}"
echo -e "  • Test renewal:     ${YELLOW}$COMPOSE_CMD -f docker-compose.prod.yml exec certbot certbot renew --dry-run${NC}"
echo -e "  • View certificate: ${YELLOW}$COMPOSE_CMD -f docker-compose.prod.yml exec certbot certbot certificates${NC}"