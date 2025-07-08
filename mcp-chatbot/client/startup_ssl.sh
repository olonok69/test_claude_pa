#!/bin/bash

# Startup script for Streamlit with SSL support
# This script handles both HTTP and HTTPS modes

echo "🚀 CSM MCP Servers - Starting Application..."

# Check if SSL is enabled
if [ "$SSL_ENABLED" = "true" ]; then
    echo "🔒 SSL mode enabled"
    
    # Generate certificates if they don't exist
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/private.key" ]; then
        echo "📝 Generating SSL certificates..."
        
        # Create ssl directory
        mkdir -p ssl
        
        # Generate certificates using the shell script
        if [ -f "generate_ssl_certificate.sh" ]; then
            chmod +x generate_ssl_certificate.sh
            ./generate_ssl_certificate.sh
        else
            echo "❌ Certificate generation script not found"
            echo "🔄 Falling back to HTTP mode"
            SSL_ENABLED="false"
        fi
    else
        echo "✅ SSL certificates found"
    fi
    
    # Start with HTTPS if certificates exist
    if [ "$SSL_ENABLED" = "true" ] && [ -f "ssl/cert.pem" ] && [ -f "ssl/private.key" ]; then
        # Get external IP (use any of the reliable services)
        EXTERNAL_IP=$(dig +short myip.opendns.com @resolver1.opendns.com)
        echo "🔒 Starting Streamlit with HTTPS on port 8502..."
        echo "📱 Access URL: https://localhost:8502"
        echo "🌐 External Access URL: https://$EXTERNAL_IP:8502"
        echo "⚠️  Browser will show security warning for self-signed certificate"
        echo "   Click 'Advanced' -> 'Proceed to localhost (unsafe)' to continue"
        echo ""
        
        exec streamlit run app.py \
            --server.port=8502 \
            --server.address=0.0.0.0 \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            --server.sslCertFile=ssl/cert.pem \
            --server.sslKeyFile=ssl/private.key
    fi
fi

# Default to HTTP mode
echo "🌐 Starting Streamlit with HTTP on port 8501..."
echo "📱 Access URL: http://localhost:8501"
echo ""

exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0