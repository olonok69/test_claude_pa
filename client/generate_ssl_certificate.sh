#!/bin/bash

# Script to generate self-signed SSL certificate for Streamlit app
# Run this script in the client directory

echo "🔒 Generating self-signed SSL certificate for Streamlit app..."

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out ssl/private.key 2048

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new -key ssl/private.key -out ssl/cert.csr -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost"

# Generate self-signed certificate
echo "📝 Generating self-signed certificate..."
openssl x509 -req -days 365 -in ssl/cert.csr -signkey ssl/private.key -out ssl/cert.pem

# Set appropriate permissions
chmod 600 ssl/private.key
chmod 644 ssl/cert.pem

# Clean up CSR file
rm ssl/cert.csr

echo "✅ SSL certificate generated successfully!"
echo "📄 Certificate: ssl/cert.pem"
echo "🔑 Private key: ssl/private.key"
echo ""
echo "⚠️  Note: This is a self-signed certificate."
echo "   Browsers will show a security warning that you'll need to accept."
echo ""
echo "🚀 You can now run: streamlit run app.py --server.enableCORS=false --server.enableXsrfProtection=false --server.sslCertFile=ssl/cert.pem --server.sslKeyFile=ssl/private.key"