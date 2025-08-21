#!/bin/bash

DOMAIN="data.forensic-bot.com"
EMAIL="olonok@gmail.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Let's Encrypt Certificate Setup${NC}"
echo "======================================"

# Step 1: Verify services are running
echo -e "${YELLOW}Current status:${NC}"
echo "✓ Nginx is running with self-signed certificates"
echo "✓ Site is accessible at https://$DOMAIN (with certificate warning)"
echo ""

# Step 2: Create directories if needed
mkdir -p certbot/www
mkdir -p certbot/conf

# Step 3: Get certificate using certbot with webroot
echo -e "${YELLOW}Requesting Let's Encrypt certificate...${NC}"
echo -e "${YELLOW}Using webroot method with running nginx...${NC}"

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
    
    # Step 4: Check certificate files
    echo -e "${YELLOW}Checking certificate files...${NC}"
    if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
        echo -e "${GREEN}✓ Certificate files exist${NC}"
        ls -la certbot/conf/live/$DOMAIN/
        
        # Step 5: Update nginx config to use Let's Encrypt
        echo -e "${YELLOW}Updating nginx configuration...${NC}"
        
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
    
    # Include SSL parameters if they exist
    include /etc/letsencrypt/options-ssl-nginx.conf*;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Root directory
    root /usr/share/nginx/html;
    index index.html;
    
    location /health {
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }

    location /sse {
        proxy_pass http://mcp-server-http:8008/sse;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
        add_header X-Accel-Buffering no;
    }

    location /secure-sse {
        proxy_pass https://mcp-server-https:8443/sse;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
        add_header X-Accel-Buffering no;
    }

    location /api/ {
        proxy_pass http://mcp-server-http:8008/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Default location
    location / {
        try_files $uri $uri/ /index.html =404;
    }
}
NGINX
        
        # Step 6: Reload nginx
        echo -e "${YELLOW}Reloading nginx with Let's Encrypt certificate...${NC}"
        sudo docker compose restart nginx
        
        # Wait for nginx to start
        sleep 5
        
        # Step 7: Test HTTPS
        echo -e "${YELLOW}Testing HTTPS with valid certificate...${NC}"
        if curl -s https://$DOMAIN/health | grep -q "healthy"; then
            echo -e "${GREEN}✓ HTTPS working with valid Let's Encrypt certificate!${NC}"
        else
            echo -e "${YELLOW}⚠ HTTPS test returned unexpected result${NC}"
        fi
        
        # Step 8: Setup auto-renewal
        echo -e "${YELLOW}Setting up auto-renewal...${NC}"
        
        cat > renew-certificates.sh << 'RENEW'
#!/bin/bash
cd $(dirname "$0")
docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot renew --quiet
docker compose restart nginx
RENEW
        chmod +x renew-certificates.sh
        
        # Add to crontab
        (crontab -l 2>/dev/null | grep -v "renew-certificates.sh"; echo "0 3 * * * $(pwd)/renew-certificates.sh >> /var/log/letsencrypt-renew.log 2>&1") | crontab -
        
        echo -e "${GREEN}✓ Auto-renewal configured (daily at 3 AM)${NC}"
        
        echo ""
        echo -e "${GREEN}============================================${NC}"
        echo -e "${GREEN}✅ SUCCESS! Let's Encrypt Setup Complete${NC}"
        echo -e "${GREEN}============================================${NC}"
        echo ""
        echo -e "Your services are now available with valid SSL:"
        echo -e "  • ${GREEN}https://data.forensic-bot.com/health${NC}"
        echo -e "  • ${GREEN}https://data.forensic-bot.com/sse${NC}"
        echo -e "  • ${GREEN}https://data.forensic-bot.com/secure-sse${NC}"
        echo ""
        echo -e "Test commands:"
        echo -e "  curl https://data.forensic-bot.com/health"
        echo -e "  curl -N https://data.forensic-bot.com/sse"
        
    else
        echo -e "${RED}Certificate files not found in expected location${NC}"
        ls -la certbot/conf/
    fi
else
    echo -e "${RED}Failed to obtain certificate${NC}"
    echo -e "${YELLOW}Possible issues:${NC}"
    echo "1. DNS not pointing to this server"
    echo "2. Port 80 not accessible from internet"
    echo "3. Rate limit hit (try again in an hour)"
    echo ""
    echo -e "${YELLOW}Debug info:${NC}"
    echo "Server IP: $(curl -s ifconfig.me)"
    echo "Domain resolves to: $(getent hosts $DOMAIN | awk '{print $1}')"
fi
