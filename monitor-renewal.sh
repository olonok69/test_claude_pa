#!/bin/bash

# Check certificate expiration
DOMAIN="data.forensic-bot.com"
COMPOSE_CMD="docker compose"

echo "Certificate Status for $DOMAIN"
echo "======================================"

# Show certificate details
$COMPOSE_CMD -f docker-compose.prod.yml exec certbot certbot certificates

# Test renewal (dry run)
echo ""
echo "Testing renewal process (dry-run):"
$COMPOSE_CMD -f docker-compose.prod.yml exec certbot certbot renew --dry-run

# Check next renewal
echo ""
echo "Next renewal check will run automatically within 12 hours"