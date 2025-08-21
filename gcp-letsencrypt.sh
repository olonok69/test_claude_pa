#!/bin/bash

DOMAIN="data.forensic-bot.com"
EMAIL="olonok@gmail.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Let's Encrypt Setup for GCP${NC}"
echo "======================================"

# Step 1: Check and open GCP firewall rules
echo -e "${YELLOW}Step 1: Checking GCP firewall rules...${NC}"

# Check if firewall rules exist
if gcloud compute firewall-rules describe allow-http &>/dev/null; then
    echo -e "${GREEN}✓ HTTP firewall rule exists${NC}"
else
    echo -e "${YELLOW}Creating HTTP firewall rule...${NC}"
    gcloud compute firewall-rules create allow-http \
        --allow tcp:80 \
        --source-ranges 0.0.0.0/0 \
        --target-tags http-server
fi

if gcloud compute firewall-rules describe allow-https &>/dev/null; then
    echo -e "${GREEN}✓ HTTPS firewall rule exists${NC}"
else
    echo -e "${YELLOW}Creating HTTPS firewall rule...${NC}"
    gcloud compute firewall-rules create allow-https \
        --allow tcp:443 \
        --source-ranges 0.0.0.0/0 \
        --target-tags https-server
fi

# Step 2: Setup nginx for HTTP challenge
echo -e "${YELLOW}Step 2: Setting up nginx for HTTP challenge...${NC}"

# Create directories
mkdir -p certbot/www
mkdir -p certbot/conf
mkdir -p nginx/conf.d

# Create HTTP-only config for challenge
cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name data.forensic-bot.com;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }
    
    # Default location
    location / {
        return 200 'Server is ready for Let\'s Encrypt\n';
        add_header Content-Type text/plain;
    }
}
NGINX

# Create temporary docker-compose for Let's Encrypt
cat > docker-compose-temp.yml << 'COMPOSE'
services:
  nginx-temp:
    image: nginx:alpine
    container_name: nginx-letsencrypt
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/www:/var/www/certbot:ro
    restart: unless-stopped
COMPOSE

# Stop any existing nginx containers
echo -e "${YELLOW}Stopping existing services...${NC}"
sudo docker stop nginx-forensic-bot 2>/dev/null || true
sudo docker stop nginx-letsencrypt 2>/dev/null || true

# Start temporary nginx
echo -e "${YELLOW}Starting temporary nginx for challenge...${NC}"
sudo docker compose -f docker-compose-temp.yml up -d

# Wait for nginx to start
sleep 5

# Step 3: Test HTTP accessibility
echo -e "${YELLOW}Step 3: Testing HTTP access...${NC}"

# Create test file
echo "test" > certbot/www/test.txt

# Test local access
if curl -f http://localhost/.well-known/acme-challenge/test.txt 2>/dev/null; then
    echo -e "${GREEN}✓ Local HTTP access working${NC}"
else
    echo -e "${RED}✗ Local HTTP access failed${NC}"
fi

# Test external access
EXTERNAL_IP=$(curl -s ifconfig.me)
echo -e "Your server IP: ${GREEN}$EXTERNAL_IP${NC}"

DNS_IP=$(dig +short $DOMAIN | head -n1)
echo -e "Domain points to: ${GREEN}$DNS_IP${NC}"

if [ "$EXTERNAL_IP" != "$DNS_IP" ]; then
    echo -e "${RED}WARNING: DNS mismatch!${NC}"
    echo -e "${YELLOW}Your domain points to $DNS_IP but your server IP is $EXTERNAL_IP${NC}"
    echo -e "${YELLOW}Please update your DNS A record to point to $EXTERNAL_IP${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Request Let's Encrypt certificate
echo -e "${YELLOW}Step 4: Requesting Let's Encrypt certificate...${NC}"

sudo docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot \
    certonly --webroot \
    -w /var/www/certbot \
    --email $EMAIL \
    -d $DOMAIN \
    --agree-tos \
    --no-eff-email \
    --force-renewal

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certificate obtained successfully!${NC}"
    
    # Step 5: Update nginx config for HTTPS
    echo -e "${YELLOW}Step 5: Configuring nginx for HTTPS...${NC}"
    
    cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name data.forensic-bot.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name data.forensic-bot.com;

    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location /health {
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }

    location /sse {
        proxy_pass http://mcp-server-http:8008/sse;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
    }

    location /secure-sse {
        proxy_pass https://mcp-server-https:8443/sse;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
    }
}
NGINX
    
    # Stop temporary nginx
    echo -e "${YELLOW}Stopping temporary nginx...${NC}"
    sudo docker compose -f docker-compose-temp.yml down
    
    # Download TLS parameters if not exist
    if [ ! -f "certbot/conf/options-ssl-nginx.conf" ]; then
        curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > certbot/conf/options-ssl-nginx.conf
    fi
    if [ ! -f "certbot/conf/ssl-dhparams.pem" ]; then
        curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > certbot/conf/ssl-dhparams.pem
    fi
    
    # Step 6: Update main docker-compose
    echo -e "${YELLOW}Step 6: Updating main docker-compose...${NC}"
    
    # Add certbot volumes to nginx in main docker-compose
    if ! grep -q "certbot/conf" docker-compose.yml; then
        echo -e "${YELLOW}Adding certbot volumes to docker-compose.yml...${NC}"
        # Backup original
        cp docker-compose.yml docker-compose.yml.bak
        
        # You may need to manually add these lines to your nginx service:
        echo -e "${YELLOW}Please manually add these volumes to your nginx service in docker-compose.yml:${NC}"
        echo "      - ./certbot/conf:/etc/letsencrypt:ro"
        echo "      - ./certbot/www:/var/www/certbot:ro"
        echo ""
        read -p "Press Enter after you've added the volumes to continue..."
    fi
    
    # Step 7: Start all services
    echo -e "${YELLOW}Step 7: Starting all services with SSL...${NC}"
    sudo docker compose up -d
    
    # Add certbot for auto-renewal
    echo -e "${YELLOW}Setting up auto-renewal...${NC}"
    
    # Create renewal script
    cat > renew-cert.sh << 'RENEW'
#!/bin/bash
docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot renew --quiet
docker compose exec nginx nginx -s reload
RENEW
    chmod +x renew-cert.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 0,12 * * * cd $(pwd) && ./renew-cert.sh >> /var/log/letsencrypt-renew.log 2>&1") | crontab -
    
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}✓ SSL Setup Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "Your services are available at:"
    echo -e "  ${GREEN}https://data.forensic-bot.com/health${NC}"
    echo -e "  ${GREEN}https://data.forensic-bot.com/sse${NC}"
    echo -e "  ${GREEN}https://data.forensic-bot.com/secure-sse${NC}"
    echo ""
    echo -e "${YELLOW}Certificate will auto-renew twice daily${NC}"
    
else
    echo -e "${RED}✗ Certificate request failed!${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting steps:${NC}"
    echo "1. Check DNS: dig +short $DOMAIN"
    echo "2. Check server IP: curl ifconfig.me"
    echo "3. Check Docker logs: sudo docker logs nginx-letsencrypt"
    echo "4. Check firewall: gcloud compute firewall-rules list"
    echo "5. Verify VM tags include 'http-server' and 'https-server'"
    echo ""
    echo -e "${YELLOW}To add network tags to your VM:${NC}"
    echo "gcloud compute instances add-tags vm-forensic --tags=http-server,https-server --zone=YOUR_ZONE"
fi

# Cleanup
rm -f docker-compose-temp.yml certbot/www/test.txt
