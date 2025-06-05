# AI & ML Repository - Comprehensive Guide

A comprehensive collection of AI/ML projects showcasing cutting-edge implementations across computer vision, natural language processing, financial analysis, distributed systems, and modern AI integration patterns.

## 📋 Table of Contents

| Category | Project | Description | Documentation |
|----------|---------|-------------|---------------|
| **Medical AI** | DICOM Anonymization | DICOM medical image anonymization using Microsoft Presidio | [📖 English](DICOM_FHIR/Readme_en.md) |
| **Google AI** | Video Summarizer | AI-powered video transcription and summarization with Gemini Pro | [📖 English](Google_AI/Video_summarizer/Readme.md) |
| **Google AI** | Content Caching | Google AI Context Caching optimization with Gemini API | [📖 English](Google_AI/content_caching/Readme_en.md) |
| **Distributed OCR** | NATS OCR System | Distributed OCR system with NATS messaging and RapidOCR | [📖 English](Nats/Readme_en.md) |
| **Financial RAG** | Financial Analysis | RAG system for fundamental financial analysis with real-time data | [📖 English](RAG/Intro/Readme.md) |
| **Trading Strategy** | Bollinger RSI Strategy | Trading strategy combining Bollinger Bands and RSI crossover | [📖 English](RAG/bollinger%20z-score%20rsi%20startegy/Readme.md) |
| **Trading Analysis** | Bollinger Z-Score | Financial trading analysis with Bollinger Bands and Z-Score | [📖 English](RAG/bollinger%20z-score/Readme.md) |
| **Trading Strategy** | Bollinger Fibonacci | Advanced strategy combining Bollinger Bands and Fibonacci retracements | [📖 English](RAG/bollinger-fibonacci_retracements/Readme.md) |
| **Trading Strategy** | MACD Donchian | Combined MACD and Donchian Channels trading strategy | [📖 English](RAG/macd_downchain%20startegy/Readme.md) |
| **Graph Database** | Neo4j RAG System | Natural language interface for Neo4j graph databases | [📖 English](RAG/speak%20with%20your%20Graph%20Database/Readme.md) |
| **MCP Integration** | MCP Servers | Model Context Protocol servers for Claude AI integration | [📖 English](mcp/mcp_server/readme_en.md) |
| **MCP Development** | Python MCP Client/Server | Python-based MCP financial analysis server with SSE transport | [📖 English](mcp/python_client_server/README.md) |

## 🌟 Repository Overview

This repository represents a comprehensive exploration of modern AI/ML technologies, demonstrating practical implementations across multiple domains:

### 🏥 Medical AI & Computer Vision
- **DICOM Anonymization**: Advanced medical image processing system that automatically detects and redacts Personal Health Information (PHI) in DICOM medical images using Microsoft's Presidio framework, ensuring HIPAA compliance.

### 🤖 Google AI Ecosystem
- **Video Summarizer**: Leverage Google's Gemini 2.0 Flash model for intelligent video content analysis, providing structured summaries and complete transcriptions with cloud integration.
- **Content Caching**: Optimize token usage and reduce costs through Google's Context Caching feature, demonstrating 99.5% token reduction and 12-18x speed improvements.

### ⚡ Distributed Systems
- **NATS OCR System**: High-performance distributed OCR processing using NATS JetStream for reliable message delivery and RapidOCR for text extraction, perfect for microservice architectures.

### 💰 Financial Analysis & Trading
- **Comprehensive RAG System**: Fundamental financial analysis combining traditional techniques with modern AI/ML, featuring real-time data integration and intelligent insights.
- **Multiple Trading Strategies**: Implementation of sophisticated trading algorithms including:
  - Bollinger Bands with RSI crossover analysis
  - Z-Score statistical analysis for market positioning
  - Fibonacci retracement integration for precise entry/exit points
  - MACD and Donchian Channels combination for momentum analysis

### 🔗 Graph Databases & Knowledge Systems
- **Neo4j RAG Integration**: Natural language interface for complex graph database interactions, enabling conversational queries across interconnected data structures.

### 🔌 Model Context Protocol (MCP)
- **MCP Server Ecosystem**: Complete implementation of Anthropic's MCP standard, demonstrating the "USB-C for AI integrations" with multiple server configurations.
- **Python MCP Framework**: Advanced financial analysis server with Server-Sent Events transport, showcasing real-time AI-tool integration.

## 🛠️ Technology Stack

### Core AI/ML Frameworks
- **LangChain & LangGraph**: Advanced AI orchestration and agent workflows
- **Google Gemini Pro**: State-of-the-art language models for various applications
- **OpenAI GPT Models**: Integration with OpenAI's API for intelligent processing
- **Microsoft Presidio**: Privacy protection and PII detection framework

### Data Processing & Analytics
- **Yahoo Finance & Financial APIs**: Real-time and historical financial data
- **PyDICOM**: Medical image processing and DICOM standard compliance
- **Pandas & NumPy**: Comprehensive data manipulation and analysis
- **Plotly & Matplotlib**: Advanced data visualization and interactive charts

### Distributed Systems & Messaging
- **NATS JetStream**: High-performance distributed messaging system
- **FastAPI**: Modern, fast web framework for building APIs
- **Docker**: Containerization for scalable deployment
- **Server-Sent Events (SSE)**: Real-time bidirectional communication

### Databases & Storage
- **Neo4j**: Graph database for complex relationship modeling
- **Qdrant**: Vector database for similarity search and RAG applications
- **Google Cloud Storage**: Scalable cloud storage integration

### Development Tools
- **UV Package Manager**: Fast Python package management
- **Jupyter Notebooks**: Interactive development and documentation
- **Environment Management**: Secure configuration with environment variables

## 🚀 Key Features & Innovations

### 🔥 Advanced AI Integration Patterns
- **Retrieval-Augmented Generation (RAG)**: Multiple implementations showing different approaches to combining retrieval with generation
- **Multi-Modal AI**: Integration of text, image, and video processing capabilities
- **Agent-Based Systems**: Intelligent agents that can discover and use tools dynamically

### 📊 Sophisticated Financial Analysis
- **Multi-Indicator Strategies**: Complex trading strategies combining 3-4 technical indicators
- **Scoring Systems**: Standardized (-100 to +100) scoring for consistent signal interpretation
- **Real-Time Processing**: Live market data integration with intelligent analysis

### 🏗️ Production-Ready Architecture
- **Microservice Design**: Distributed systems with clear separation of concerns
- **Security Best Practices**: Proper authentication, authorization, and data protection
- **Scalable Infrastructure**: Cloud-native designs with containerization support

### 🔧 Developer Experience
- **Comprehensive Documentation**: Detailed READMEs with setup instructions and examples
- **Interactive Notebooks**: Jupyter notebooks for learning and experimentation
- **Type Safety**: Python type hints and schema validation throughout

## 🎯 Use Cases & Applications

### Healthcare & Medical
- **Medical Image Anonymization**: HIPAA-compliant processing of medical images
- **Clinical Workflow Integration**: Seamless integration with existing medical systems

### Financial Services
- **Algorithmic Trading**: Automated trading signal generation and analysis
- **Risk Assessment**: Advanced risk metrics and portfolio analysis
- **Market Research**: Intelligent analysis of financial trends and patterns

### Enterprise AI
- **Document Processing**: Automated extraction and analysis of business documents
- **Knowledge Management**: Graph-based knowledge systems for complex data relationships
- **AI-Powered Analytics**: Integration of AI capabilities into existing business workflows

### Media & Content
- **Video Analysis**: Automated transcription, summarization, and content analysis
- **Real-Time Processing**: Live content analysis and intelligent insights

## 🚦 Getting Started

### Quick Setup
1. **Choose Your Domain**: Select a project from the table above based on your interests
2. **Follow Documentation**: Each project has comprehensive setup instructions
3. **Environment Setup**: Most projects use Python with specific dependency management
4. **API Keys**: Secure your API keys in environment variables

### Recommended Learning Path
1. **Start with RAG Systems**: Begin with the Financial Analysis RAG for foundational concepts
2. **Explore Trading Strategies**: Progress through the different trading algorithm implementations
3. **Advanced Integration**: Move to MCP servers for understanding modern AI integration patterns
4. **Specialized Applications**: Dive into domain-specific applications like medical AI or distributed OCR



### Research Areas
- **Multimodal AI**: Advanced integration of different AI modalities
- **Federated Learning**: Distributed machine learning implementations
- **Edge Computing**: Edge-deployed AI processing capabilities
- **Quantum Computing**: Quantum-enhanced algorithms for optimization

## ⚖️ License & Disclaimer

This repository contains educational and research implementations. Individual projects may have specific licensing terms. Please review each project's documentation for:

- **Usage Rights**: Appropriate use cases and restrictions
- **API Terms**: Third-party service terms and conditions
- **Financial Disclaimer**: Investment and trading risk warnings
- **Medical Disclaimer**: Healthcare application limitations

---

**This repository represents the convergence of traditional domain expertise with cutting-edge AI capabilities, demonstrating how modern AI systems can be integrated into real-world applications while maintaining production-quality standards and best practices.**