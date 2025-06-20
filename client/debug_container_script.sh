#!/bin/bash

# Debug script to check container setup
echo "🔍 Container Debug Information"
echo "=============================="

echo "📁 Current working directory: $(pwd)"
echo ""

echo "📄 Files in current directory:"
ls -la
echo ""

echo "🔧 Checking for startup scripts:"
echo "startup_ssl.sh exists: $([ -f startup_ssl.sh ] && echo 'YES' || echo 'NO')"
echo "startup_ssl.sh permissions: $([ -f startup_ssl.sh ] && ls -l startup_ssl.sh || echo 'N/A')"
echo "generate_ssl_certificate.sh exists: $([ -f generate_ssl_certificate.sh ] && echo 'YES' || echo 'NO')"
echo "generate_ssl_certificate.py exists: $([ -f generate_ssl_certificate.py ] && echo 'YES' || echo 'NO')"
echo ""

echo "📊 Environment variables:"
echo "SSL_ENABLED: ${SSL_ENABLED:-not set}"
echo "OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo 'SET' || echo 'NOT SET')"
echo ""

echo "🐍 Python and Streamlit check:"
python --version
streamlit --version
echo ""

echo "📁 SSL directory status:"
if [ -d "ssl" ]; then
    echo "SSL directory exists:"
    ls -la ssl/
else
    echo "SSL directory does not exist"
fi
echo ""

echo "🔧 Trying to run startup script manually:"
if [ -f "startup_ssl.sh" ]; then
    echo "Script content (first 10 lines):"
    head -10 startup_ssl.sh
    echo ""
    echo "Testing script execution:"
    bash -x startup_ssl.sh
else
    echo "startup_ssl.sh not found!"
    echo "Available .sh files:"
    find . -name "*.sh" -type f
fi
