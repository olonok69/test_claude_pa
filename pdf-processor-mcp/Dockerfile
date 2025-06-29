# PDF Document Processor MCP Server Docker Image

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pdf_processor_server.py .
COPY prompts.json .

# Create directory for temporary files
RUN mkdir -p /tmp/pdf_processor

# Set environment variables
ENV PYTHONPATH=/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Expose port (if running as HTTP server in the future)
EXPOSE 8000

# Run the server
CMD ["python", "pdf_processor_server.py"]