#!/bin/bash

# Installation script for PDF Document Processor MCP Server

echo "Installing PDF Document Processor MCP Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Install system dependencies for OCR
echo "Installing system dependencies..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux system"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
    elif command -v yum &> /dev/null; then
        sudo yum install -y tesseract tesseract-langpack-spa tesseract-langpack-eng
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y tesseract tesseract-langpack-spa tesseract-langpack-eng
    else
        echo "Warning: Could not detect package manager. Please install tesseract-ocr manually."
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    if command -v brew &> /dev/null; then
        brew install tesseract tesseract-lang
    else
        echo "Warning: Homebrew not found. Please install tesseract manually or install Homebrew first."
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    echo "Detected Windows system"
    echo "Please manually install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki"
    echo "Make sure to add Tesseract to your PATH"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Test tesseract installation
echo "Testing Tesseract installation..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version | head -n1)
    echo "Tesseract installed: $tesseract_version"
else
    echo "Warning: Tesseract not found in PATH. OCR functionality may not work."
fi

# Test the server
echo "Testing server installation..."
python pdf_processor_server.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Server installation successful!"
else
    echo "⚠️  Server installation may have issues. Check the logs above."
fi

echo ""
echo "Installation complete!"
echo ""
echo "To run the server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the server: python pdf_processor_server.py"
echo ""
echo "For Claude Desktop integration, add this to your configuration:"
echo "{"
echo "  \"mcpServers\": {"
echo "    \"pdf-processor\": {"
echo "      \"command\": \"python\","
echo "      \"args\": [\"$(pwd)/pdf_processor_server.py\"]"
echo "    }"
echo "  }"
echo "}"