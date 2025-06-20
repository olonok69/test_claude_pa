#!/bin/bash

# Startup script for Streamlit with SSL support
# This script handles both HTTP and HTTPS modes

echo "🚀 CSM MCP Servers - Starting Application..."
echo "Working directory: $(pwd)"
echo "Available files: $(ls -la)"

# Check if SSL is enabled
if [ "$SSL_ENABLED" = "true" ]; then
    echo "🔒 SSL mode enabled"
    
    # Generate certificates if they don't exist
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/private.key" ]; then
        echo "📝 Generating SSL certificates..."
        
        # Create ssl directory
        mkdir -p ssl
        
        # Try Python certificate generator first
        if [ -f "generate_ssl_certificate.py" ]; then
            echo "Using Python certificate generator..."
            python generate_ssl_certificate.py
        # Fallback to shell script
        elif [ -f "generate_ssl_certificate.sh" ]; then
            echo "Using shell certificate generator..."
            chmod +x generate_ssl_certificate.sh
            ./generate_ssl_certificate.sh
        else
            echo "❌ No certificate generation script found"
            echo "🔄 Falling back to HTTP mode"
            SSL_ENABLED="false"
        fi
    else
        echo "✅ SSL certificates found"
        echo "Certificate details:"
        ls -la ssl/
    fi
    
    # Start with HTTPS if certificates exist
    if [ "$SSL_ENABLED" = "true" ] && [ -f "ssl/cert.pem" ] && [ -f "ssl/private.key" ]; then
        echo "🔒 Starting Streamlit with HTTPS on port 8502..."
        echo "📱 Access URL: https://localhost:8502"
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