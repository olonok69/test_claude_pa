#!/bin/bash
cd $(dirname "$0")
docker run --rm \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    certbot/certbot renew --quiet
docker compose restart nginx
