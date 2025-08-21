#!/bin/bash

# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/data.forensic-bot.com.key \
    -out nginx/ssl/data.forensic-bot.com.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=data.forensic-bot.com"

# Set permissions
chmod 644 nginx/ssl/data.forensic-bot.com.crt
chmod 600 nginx/ssl/data.forensic-bot.com.key

echo "Self-signed certificate generated successfully!"