#!/bin/bash

DOMAIN="data.forensic-bot.com"
EMAIL="olonok@gmail.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Getting Let's Encrypt Certificate${NC}"
echo "======================================"

# Step 1: Ensure directories exist
mkdir -p certbot/www
mkdir -p certbot/conf

# Step 2: Verify nginx is running
if ! sudo docker ps | grep -q nginx-forensic-bot; then
    echo -e "${RED}Nginx not running. Starting it...${NC}"
    sudo docker compose up -d nginx
    sleep 5
fi

# Step 3: Test HTTP access
echo -e "${YELLOW}Testing HTTP access...${NC}"
if curl -f http://localhost/.well-known/acme-challenge/test 2>/dev/null; then
    echo -e "${GREEN}✓ HTTP challenge path accessible${NC}"
else
    echo -e "${YELLOW}HTTP challenge path not accessible, but continuing...${NC}"
fi

# Step 4: Request certificate using standalone mode
echo -e "${YELLOW}Requesting certificate...${NC}"

# Stop nginx temporarily to use standalone mode
sudo docker compose stop nginx

# Use standalone mode (certbot will create its own webserver)
sudo docker run --rm \
    -p 80:80 \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot \
    certonly --standalone \
    --email $EMAIL \
    -d $DOMAIN \
    --agree-tos \
    --no-eff-email \
    --force-renewal

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certificate obtained successfully!${NC}"
    
    # Step 5: Update nginx config to use Let's Encrypt
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

    # Let's Encrypt certificates
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
    
    # Step 6: Start nginx with Let's Encrypt cert
    echo -e "${YELLOW}Starting nginx with Let's Encrypt certificate...${NC}"
    sudo docker compose up -d nginx
    
    # Wait and check
    sleep 5
    if sudo docker ps | grep -q nginx-forensic-bot; then
        echo -e "${GREEN}✓ Nginx started successfully!${NC}"
        echo ""
        echo -e "${GREEN}Your site is now available with valid SSL:${NC}"
        echo "  https://data.forensic-bot.com/health"
        echo "  https://data.forensic-bot.com/sse"
        echo ""
        
        # Setup auto-renewal
        echo -e "${YELLOW}Setting up auto-renewal...${NC}"
        cat > renew-cert.sh << 'RENEW'
#!/bin/bash
sudo docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot renew --quiet
sudo docker compose restart nginx
RENEW
        chmod +x renew-cert.sh
        
        # Add to crontab
        (crontab -l 2>/dev/null; echo "0 3 * * * cd $(pwd) && ./renew-cert.sh") | crontab -
        
        echo -e "${GREEN}✓ Auto-renewal configured${NC}"
    else
        echo -e "${RED}Nginx failed to start. Check logs:${NC}"
        sudo docker compose logs nginx
    fi
else
    echo -e "${RED}Certificate request failed!${NC}"
    echo -e "${YELLOW}Starting nginx with self-signed cert...${NC}"
    sudo docker compose up -d nginx
fi
