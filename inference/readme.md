# Inference System

This folder contains various implementations for running large language model (LLM) inference, with a focus on profile classification tasks. The system supports multiple inference backends including vLLM, Ollama, OpenAI, Azure OpenAI, and Google Gemini.

## 📁 Folder Structure

```
inference/
├── inference_vllm.md           # Documentation about vLLM framework
├── llama_class*.py            # Various inference implementations
├── req_vllm.py                # Direct vLLM usage example
└── vllm.ipynb                 # Jupyter notebook for vLLM experiments
```

## 🚀 Key Components

### 1. vLLM Documentation (`inference_vllm.md`)

Comprehensive documentation covering:
- **vLLM Framework**: High-performance LLM serving library optimized for production
- **KV Cache**: Explanation of key-value caching for efficient attention computation
- **Paged Attention**: Memory optimization technique for handling multiple concurrent requests
- **Installation and usage instructions**
- **Comparison with other frameworks (Ollama)**

### 2. Profile Classification Scripts

The system includes multiple implementations for classifying profiles using different approaches:

#### Synchronous Implementations
- `llama_class_2.py` - Basic synchronous classification using local vLLM server
- `llama_class3_openai.py` - OpenAI API integration
- `llama_class3_azure_openai.py` - Azure OpenAI integration
- `llama_class3_gemini.py` - Google Gemini integration

#### Asynchronous Implementations
- `llama_class_async.py` - Basic async using Ollama AsyncClient
- `llama_class_async_2.py` - Async with Langchain integration
- `llama_class_async_3.py` - Enhanced async with detailed logging
- `llama_class_async_4.py` - Multi-server async implementation
- `llama_class_async_5.py` - Async with server load balancing

#### Parallel Processing
- `llama_class_multi.py` - Multiprocessing implementation for parallel inference

### 3. vLLM Examples
- `req_vllm.py` - Direct vLLM library usage example
- `vllm.ipynb` - Jupyter notebook with ngrok integration for remote access

## 🔧 Features

### Profile Classification System
- **Template-based prompting**: Uses `LLama_PromptTemplate` for consistent prompt generation
- **Batch processing**: Handles multiple profiles efficiently
- **Cost tracking**: Monitors token usage and calculates inference costs
- **Status handling**: Manages profiles with different data availability statuses
- **Output formatting**: Structured JSON responses with categories and certainty levels

### Supported Models
- Llama 3.1 (8B, various quantizations)
- GPT-4o-mini (OpenAI)
- Azure OpenAI deployments
- Gemini 2.0 Flash Lite

### Performance Optimizations
- **Async processing**: Multiple async implementations for concurrent inference
- **Multi-server support**: Load balancing across multiple Ollama instances
- **Batch processing**: Efficient handling of multiple requests
- **Memory optimization**: Paged attention for better GPU utilization

## 📋 Configuration

The scripts use environment variables (`.env` file) for configuration:
```env
# API Keys
OPENAI_API_KEY=your_openai_key
AZURE_API_KEY=your_azure_key
AZURE_ENDPOINT=your_azure_endpoint
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=your_api_version
GEMINI_API_KEY=your_gemini_key
NGROK=your_ngrok_token
```

## 🚦 Usage Examples

### Basic vLLM Server
```bash
vllm serve /path/to/model.gguf \
    --tokenizer /path/to/tokenizer \
    --max_model_len 10000 \
    --dtype auto
```

### Running Classification
```python
# Synchronous
python llama_class3_openai.py

# Asynchronous with multiple servers
python llama_class_async_5.py

# Multiprocessing
python llama_class_multi.py
```

## 📊 Output Format

Classification results are saved as JSON files with the following structure:
```json
{
    "profile_id": "unique_id",
    "response": {
        "category": "predicted_category",
        "ranked_categories": ["cat1", "cat2"],
        "certainty": "high/medium/low"
    },
    "input": "original_profile_data"
}
```

## 🔍 Key Concepts

### KV Cache Optimization
- Reduces redundant computation in autoregressive generation
- Caches key and value states for previous tokens
- Significantly speeds up inference at the cost of memory

### Paged Attention
- Non-contiguous memory allocation for KV cache
- Better memory utilization and support for more concurrent requests
- Inspired by virtual memory paging in operating systems

### Cost Calculation
- Tracks input and output tokens
- Calculates costs based on provider-specific pricing
- Helps monitor and optimize inference expenses

## 🛠️ Dependencies

- `langchain` - LLM orchestration framework
- `langchain-openai` - OpenAI/Azure integration
- `langchain-google-genai` - Gemini integration
- `langchain-ollama` - Ollama integration
- `vllm` - High-performance inference engine
- `ollama` - Local LLM serving
- `asyncio` - Asynchronous programming
- `httpx` - Async HTTP client
- Additional utilities from `src.classes` and `src.conf`

## 📝 Notes

- The system assumes specific data structures for profiles and status tracking
- Logging is configured with color-coded output for better debugging
- Multiple inference strategies allow choosing the best approach for your use case
- Cost tracking helps optimize token usage across different providers