
#!/bin/bash

# Configuration
domain="data.forensic-bot.com"
rsa_key_size=4096
data_path="./certbot"
email="olonok@gmail.com" # CHANGE THIS TO YOUR EMAIL
staging=0 # Set to 1 if testing

# Create required directories
echo "### Creating required directories..."
mkdir -p "$data_path/conf"
mkdir -p "$data_path/www"

# Download recommended TLS parameters
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters..."
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
fi

# Create dummy certificate for nginx to start
echo "### Creating dummy certificate for $domain..."
path="/etc/letsencrypt/live/$domain"
mkdir -p "$data_path/conf/live/$domain"

# Generate dummy certificate
docker run --rm -v $(pwd)/certbot/conf:/etc/letsencrypt \
  --entrypoint "openssl" certbot/certbot \
  req -x509 -nodes -newkey rsa:1024 -days 1 \
  -keyout "$path/privkey.pem" \
  -out "$path/fullchain.pem" \
  -subj "/CN=localhost"

echo "### Starting nginx with dummy certificate..."
