#!/bin/bash

DOMAIN="data.forensic-bot.com"

echo "Testing SSL certificate for $DOMAIN"
echo "=========================================="

# Test certificate validity
echo "1. Certificate dates:"
echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates

echo ""
echo "2. Certificate issuer:"
echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -issuer

echo ""
echo "3. Testing endpoints:"
echo -n "  • Health check: "
curl -s https://$DOMAIN/health

echo -n "  • HTTP redirect: "
curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN

echo ""
echo ""
echo "4. SSL Labs test:"
echo "  Visit: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"