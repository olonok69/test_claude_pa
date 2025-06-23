#!/bin/bash

# Session Recommendations Dependencies Installer
echo "Installing session recommendations dependencies..."

# Set environment variables to avoid conflicts
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1

# Upgrade pip first
pip install --upgrade pip

# Install core dependencies
echo "Installing core dependencies..."
pip install neo4j>=5.0.0
pip install scikit-learn>=1.3.0

# Install PyTorch with specific version to avoid conflicts
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers
echo "Installing sentence-transformers..."
pip install sentence-transformers>=2.2.0

# Optional: Install LangChain dependencies
echo "Installing optional LangChain dependencies..."
pip install langchain>=0.1.0 langchain-openai>=0.1.0 langchain-core>=0.1.0 azure-ai-inference>=1.0.0 azure-core>=1.28.0

echo "Installation complete!"
echo ""
echo "If you encounter PyTorch conflicts, try:"
echo "pip uninstall torch torchvision torchaudio"
echo "pip install torch --no-cache-dir"