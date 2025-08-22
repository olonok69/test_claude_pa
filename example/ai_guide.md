# Dual Moving Average AI Agent - Setup Guide

This guide helps you set up the Dual Moving Average AI Agent with support for both OpenAI (GPT) and Google Vertex AI (Gemini) models.

## 📋 Environment Configuration

Create a `.env` file in your project directory with the following configuration:

### Option 1: OpenAI Configuration
```bash
# Model Provider (choose one: "openai" or "vertexai")
MODEL_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

### Option 2: Vertex AI (Gemini) Configuration
```bash
# Model Provider
MODEL_PROVIDER=vertexai

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

## 🔧 Installation Instructions

### Base Dependencies
```bash
# Core dependencies (required for both providers)
pip install pandas numpy yfinance langchain langgraph python-dotenv
```

### Provider-Specific Dependencies

#### For OpenAI:
```bash
pip install langchain-openai
```

#### For Vertex AI (Gemini):
```bash
pip install langchain-google-vertexai google-cloud-aiplatform
```

### Complete Installation
```bash
# Install all dependencies at once
pip install pandas numpy yfinance langchain langgraph python-dotenv langchain-openai langchain-google-vertexai google-cloud-aiplatform
```

## 🚀 Setup Instructions

### OpenAI Setup

1. **Get API Key:**
   - Visit [OpenAI API](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key to your `.env` file

2. **Test Connection:**
   ```python
   from dual_ma_agent import test_model_connection
   test_model_connection()
   ```

### Vertex AI (Gemini) Setup

#### Option A: Service Account Authentication (Recommended for Production)

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Note your project ID

2. **Enable Required APIs:**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable vertexai.googleapis.com
   ```

3. **Create Service Account:**
   ```bash
   # Create service account
   gcloud iam service-accounts create vertex-ai-agent \
       --description="Service account for Dual MA AI Agent" \
       --display-name="Vertex AI Agent"

   # Grant necessary roles
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:vertex-ai-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"

   # Create and download key
   gcloud iam service-accounts keys create ~/vertex-ai-key.json \
       --iam-account=vertex-ai-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Update .env file:**
   ```bash
   MODEL_PROVIDER=vertexai
   GOOGLE_CLOUD_PROJECT=your-actual-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/vertex-ai-key.json
   ```

#### Option B: User Authentication (Quick Setup for Development)

1. **Install Google Cloud SDK:**
   - Download from [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Update .env file:**
   ```bash
   MODEL_PROVIDER=vertexai
   GOOGLE_CLOUD_PROJECT=your-actual-project-id
   # No need for GOOGLE_APPLICATION_CREDENTIALS with this method
   ```

## 🔄 Switching Between Providers

You can switch between OpenAI and Vertex AI at runtime:

```python
from dual_ma_agent import switch_model_provider

# Switch to Vertex AI
switch_model_provider("vertexai")

# Switch back to OpenAI
switch_model_provider("openai")
```

Or modify the `.env` file and restart the application.

## 🧪 Testing Your Setup

### Quick Test
```python
python dual_ma_agent.py
```

### Manual Test
```python
from dual_ma_agent import test_model_connection, get_llm

# Test connection
test_model_connection()

# Test basic functionality
llm = get_llm()
response = llm.invoke("Explain the golden cross pattern in trading")
print(response.content)
```

## 📊 Model Comparison

| Feature | OpenAI GPT-4o-mini | Vertex AI Gemini-1.5-Pro |
|---------|-------------------|---------------------------|
| **Speed** | Fast | Very Fast |
| **Cost** | Low | Very Low |
| **Context** | 128K tokens | 2M tokens |
| **Reasoning** | Excellent | Excellent |
| **Tool Use** | Native | Native |
| **Multimodal** | Yes | Yes |

### Recommended Usage:

- **OpenAI**: Better for complex financial reasoning and consistent output formatting
- **Vertex AI**: Better for high-volume analysis, longer context, and cost efficiency

## 🚨 Troubleshooting

### Common Issues:

#### 1. Authentication Errors (Vertex AI)
```bash
# Check authentication
gcloud auth list
gcloud config get-value project

# Re-authenticate if needed
gcloud auth application-default login
```

#### 2. API Not Enabled
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable vertexai.googleapis.com
```

#### 3. Permission Errors
```bash
# Check IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --format='table(bindings.role)'
```

#### 4. Import Errors
```bash
# Reinstall langchain packages
pip uninstall langchain-google-vertexai
pip install langchain-google-vertexai --upgrade
```

### Environment Variables Debug:
```python
import os
print("Model Provider:", os.getenv("MODEL_PROVIDER"))
print("GCP Project:", os.getenv("GOOGLE_CLOUD_PROJECT"))
print("Credentials Path:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("OpenAI Key Set:", bool(os.getenv("OPENAI_API_KEY")))
```

## 💡 Best Practices

### Security:
- Never commit `.env` files to version control
- Use service accounts for production
- Rotate API keys regularly
- Set up billing alerts

### Performance:
- Use Gemini Flash for simple queries
- Use Gemini Pro for complex analysis
- Batch multiple symbol analyses
- Cache frequently requested data

### Cost Optimization:
- Monitor token usage
- Use appropriate model sizes
- Implement response caching
- Set usage limits

## 📖 Example Usage

### Basic Analysis:
```python
from dual_ma_agent import analyze_stock_dual_ma

result = analyze_stock_dual_ma("AAPL", period="1y")
print(result)
```

### Market Scanner:
```python
from dual_ma_agent import scan_market_opportunities

stocks = ["AAPL", "MSFT", "GOOGL", "TSLA"]
opportunities = scan_market_opportunities(stocks)
print(opportunities)
```

### Interactive Chat:
```python
from dual_ma_agent import create_dual_ma_agent
from langchain_core.messages import HumanMessage

graph = create_dual_ma_agent()
config = {"configurable": {"thread_id": "test"}}

result = graph.invoke({
    "messages": [HumanMessage(content="Analyze Tesla using EMA 20/50 strategy")]
}, config)

print(result["messages"][-1].content)
```

## 🔗 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your environment variables
3. Test model connections individually
4. Review API quotas and limits
5. Check Google Cloud billing status (for Vertex AI)