#!/bin/bash

DOMAIN="data.forensic-bot.com"
EMAIL="olonok@gmail.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Let's Encrypt Setup for GCP (Fixed)${NC}"
echo "======================================"

# Get IPs
EXTERNAL_IP=$(curl -s ifconfig.me)
echo -e "Your server IP: ${GREEN}$EXTERNAL_IP${NC}"

# Get DNS IP using nslookup instead of dig
DNS_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | tail -1 | awk '{print $2}')
if [ -z "$DNS_IP" ]; then
    # Try alternative method
    DNS_IP=$(getent hosts $DOMAIN | awk '{print $1}')
fi
echo -e "Domain points to: ${GREEN}$DNS_IP${NC}"

if [ "$EXTERNAL_IP" != "$DNS_IP" ]; then
    echo -e "${YELLOW}NOTE: Your domain might be using a proxy (like Cloudflare)${NC}"
    echo -e "${YELLOW}Actual server IP: $EXTERNAL_IP${NC}"
    echo -e "${YELLOW}DNS resolves to: $DNS_IP${NC}"
fi

# Step 1: Ensure firewall rules
echo -e "${YELLOW}Step 1: Setting up GCP firewall...${NC}"
gcloud compute firewall-rules create allow-http --allow tcp:80 --source-ranges 0.0.0.0/0 2>/dev/null || echo "HTTP rule exists"
gcloud compute firewall-rules create allow-https --allow tcp:443 --source-ranges 0.0.0.0/0 2>/dev/null || echo "HTTPS rule exists"

# Add tags to VM
echo -e "${YELLOW}Adding network tags to VM...${NC}"
gcloud compute instances add-tags vm-forensic --tags=http-server,https-server --zone=europe-west2-c 2>/dev/null || true

# Step 2: Check if nginx is actually running and accessible
echo -e "${YELLOW}Step 2: Checking nginx status...${NC}"

# Check if container is running
if sudo docker ps | grep -q nginx-letsencrypt; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
    
    # Check nginx logs
    echo "Recent nginx logs:"
    sudo docker logs --tail=5 nginx-letsencrypt
    
    # Test from inside the container
    echo -e "${YELLOW}Testing from inside container...${NC}"
    sudo docker exec nginx-letsencrypt sh -c "ls -la /var/www/certbot"
    sudo docker exec nginx-letsencrypt sh -c "ls -la /etc/nginx/conf.d"
else
    echo -e "${RED}✗ Nginx container not running, starting it...${NC}"
    
    # Ensure directories exist
    mkdir -p certbot/www certbot/conf nginx/conf.d
    
    # Create simple nginx config
    cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'Ready for Let\'s Encrypt\n';
        add_header Content-Type text/plain;
    }
}
NGINX
    
    # Start nginx with docker run
    sudo docker run -d \
        --name nginx-letsencrypt \
        -p 80:80 \
        -v $(pwd)/nginx/conf.d:/etc/nginx/conf.d:ro \
        -v $(pwd)/certbot/www:/var/www/certbot:ro \
        nginx:alpine
fi

# Wait for nginx
sleep 3

# Step 3: Test connectivity
echo -e "${YELLOW}Step 3: Testing connectivity...${NC}"

# Test local
if curl -f http://localhost/ 2>/dev/null | grep -q "Ready"; then
    echo -e "${GREEN}✓ Local access working${NC}"
else
    echo -e "${RED}✗ Local access failed${NC}"
    # Check what's listening on port 80
    sudo netstat -tlnp | grep :80
fi

# Test external with actual domain
echo -e "${YELLOW}Testing external access to http://$DOMAIN ...${NC}"
if curl -f -m 5 http://$DOMAIN/ 2>/dev/null; then
    echo -e "${GREEN}✓ External access working${NC}"
    
    # Now request certificate
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
        echo -e "${GREEN}✓ Certificate obtained!${NC}"
        
        # Update nginx for HTTPS
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
    
    location /health {
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }

    location /sse {
        proxy_pass http://mcp-server-http:8008/sse;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        add_header Content-Type text/event-stream;
    }

    location /secure-sse {
        proxy_pass https://mcp-server-https:8443/sse;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        add_header Content-Type text/event-stream;
    }
}
NGINX
        
        # Stop temporary nginx
        sudo docker stop nginx-letsencrypt
        sudo docker rm nginx-letsencrypt
        
        # Update main docker-compose.yml
        echo -e "${YELLOW}Please add these volumes to nginx service in docker-compose.yml:${NC}"
        echo "      - ./certbot/conf:/etc/letsencrypt:ro"
        echo "      - ./certbot/www:/var/www/certbot:ro"
        echo ""
        read -p "Press Enter after adding the volumes..."
        
        # Start all services
        sudo docker compose up -d
        
        echo -e "${GREEN}✓ Setup complete!${NC}"
        echo "Test: curl https://$DOMAIN/health"
    else
        echo -e "${RED}Certificate request failed${NC}"
    fi
else
    echo -e "${RED}✗ Cannot reach http://$DOMAIN${NC}"
    echo -e "${YELLOW}Debugging information:${NC}"
    echo "1. Check if port 80 is open:"
    sudo netstat -tlnp | grep :80
    echo ""
    echo "2. Check firewall rules:"
    gcloud compute firewall-rules list | grep -E "allow-http|allow-https"
    echo ""
    echo "3. Test with IP directly:"
    curl -v http://$EXTERNAL_IP/
fi
