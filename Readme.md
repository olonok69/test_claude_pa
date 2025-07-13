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
| **Trading Strategy** | Connors RSI Strategy | Advanced momentum oscillator with LangGraph integration for enhanced mean reversion signals | [📖 English](RAG/connor-rsi/Readme.md) |
| **Trading Strategy** | MACD Donchian | Combined MACD and Donchian Channels trading strategy | [📖 English](RAG/macd_downchain%20startegy/Readme.md) |
| **Graph Database** | Neo4j RAG System | Natural language interface for Neo4j graph databases | [📖 English](RAG/speak%20with%20your%20Graph%20Database/Readme.md) |
| **MCP Integration** | MCP Servers | Model Context Protocol servers for Claude AI integration | [📖 English](mcp/mcp_server/readme_en.md) |
| **MCP Development** | Python MCP Client/Server | Python-based MCP financial analysis server with SSE transport | [📖 English](mcp/python_client_server/README.md) |
| **MCP Client** | Multi-Language MCP Client | Comprehensive MCP client with financial analysis tools and multi-server support | [📖 English](mcp/mcp-client/README.md) |
| **MCP Chatbot** | Chainlit MCP Bot | Conversational AI chatbot integrating Neo4j and HubSpot through MCP protocol | [📖 English](mcp/chainlit_bot/README.md) |
| **MCP Platform** | Streamlit CRM & Graph Platform | Full-stack AI-powered platform integrating Neo4j, HubSpot CRM, and Yahoo Finance with enterprise authentication | [📖 English](mcp/Streamlit_chatbot/README.md) |
| **MCP Development** | Build MCP with LLMs | Comprehensive guide to accelerate MCP server development using language models like Claude, with practical PDF document processor example | [📖 English](mcp/Build%20MCP%20with%20LLMs/README.md) |
| **Claude Desktop** | Claude Desktop Setup Guide | Complete guide for Claude Desktop installation and MCP configuration | [📖 English](mcp/claude_desktop/Readme.md) |

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
  - **Bollinger Bands with RSI crossover analysis**: Multi-indicator confirmation for trending markets
  - **Z-Score statistical analysis**: Market positioning and mean reversion signals
  - **Fibonacci retracement integration**: Precise entry/exit points with advanced scoring systems
  - **Connors RSI Strategy**: Advanced momentum oscillator developed by Larry Connors combining three distinct components:
    - **Price RSI (33.33%)**: 3-day RSI for recent price momentum
    - **Streak RSI (33.33%)**: RSI applied to consecutive up/down movements
    - **Percent Rank (33.33%)**: Percentile ranking over 100-day rolling window
    - **Enhanced Features**: Z-Score integration, combined scoring system (-100 to +100), LangGraph agent integration
  - **MACD and Donchian Channels combination**: Momentum analysis with volatility indicators

### 🔗 Graph Databases & Knowledge Systems
- **Neo4j RAG Integration**: Natural language interface for complex graph database interactions, enabling conversational queries across interconnected data structures.

### 🔌 Model Context Protocol (MCP)
- **MCP Server Ecosystem**: Complete implementation of Anthropic's MCP standard, demonstrating the "USB-C for AI integrations" with multiple server configurations.
- **Python MCP Framework**: Advanced financial analysis server with Server-Sent Events transport, showcasing real-time AI-tool integration.
- **Multi-Language MCP Client**: Comprehensive client implementation bridging Claude AI with external tools, featuring specialized financial analysis capabilities across Python and Node.js servers.
- **Chainlit MCP Chatbot**: Sophisticated conversational AI application that seamlessly connects Neo4j graph databases and HubSpot CRM through the Model Context Protocol, built with Chainlit for an intuitive chat interface. Features intelligent data exploration, cross-system analysis, and natural language querying across multiple data sources.
- **Streamlit CRM & Graph Platform**: Enterprise-grade full-stack application providing AI-powered interactions with Neo4j graph databases, HubSpot CRM systems, and Yahoo Finance data through MCP servers. Features comprehensive authentication, multi-provider AI support, and production-ready architecture with 25+ specialized tools for complete data analysis, management, and automation across database, CRM, and financial data infrastructure.
- **Build MCP with LLMs**: Comprehensive guide demonstrating how to accelerate MCP server development using language models like Claude. Includes a complete practical example of a PDF document processor with OCR capabilities, custom prompts, and markdown output generation, showcasing how AI can significantly speed up MCP development workflows.
- **Claude Desktop Integration**: Complete setup guide for Claude Desktop application with MCP server configuration, enabling seamless AI-tool interactions on your desktop.

## 🛠️ Technology Stack

### Core AI/ML Frameworks
- **LangChain & LangGraph**: Advanced AI orchestration and agent workflows
- **Google Gemini Pro**: State-of-the-art language models for various applications
- **OpenAI GPT Models**: Integration with OpenAI's API for intelligent processing
- **Microsoft Presidio**: Privacy protection and PII detection framework
- **Chainlit**: Python framework for building conversational AI applications
- **Streamlit**: Python framework for building interactive web applications and data dashboards

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
- **HubSpot CRM**: Customer relationship management and sales pipeline tracking
- **Qdrant**: Vector database for similarity search and RAG applications
- **Google Cloud Storage**: Scalable cloud storage integration

#### **MCP Development**
```yaml
Framework: Model Context Protocol (Anthropic)
Languages: Python, Node.js, TypeScript
Transport: STDIO, SSE, HTTP
Tools: FastMCP, PDF processing, OCR
Development Acceleration: LLM-assisted development
```

### Development Tools
- **UV Package Manager**: Fast Python package management
- **Jupyter Notebooks**: Interactive development and documentation
- **Environment Management**: Secure configuration with environment variables

## 🚀 Key Features & Innovations

### 🔥 Advanced AI Integration Patterns
- **Retrieval-Augmented Generation (RAG)**: Multiple implementations showing different approaches to combining retrieval with generation
- **Multi-Modal AI**: Integration of text, image, and video processing capabilities
- **Agent-Based Systems**: Intelligent agents that can discover and use tools dynamically
- **Model Context Protocol**: Standardized AI-tool integration across multiple languages and platforms
- **Conversational AI**: Interactive chatbot interfaces for natural language data exploration
- **Enterprise Web Applications**: Production-ready web platforms with comprehensive authentication and multi-user support
- **LLM-Accelerated Development**: Using language models to significantly speed up MCP server development and reduce boilerplate code

### 📊 Sophisticated Financial Analysis
- **Multi-Indicator Strategies**: Complex trading strategies combining 3-4 technical indicators
- **Advanced Momentum Analysis**: Connors RSI implementation with component analysis and AI-powered recommendations
- **Scoring Systems**: Standardized (-100 to +100) scoring for consistent signal interpretation
- **Real-Time Processing**: Live market data integration with intelligent analysis
- **Cross-Platform Integration**: Financial tools accessible via multiple transport mechanisms
- **Enterprise Financial Platform**: Full-stack financial analysis with CRM integration and graph database connectivity

### 🏗️ Production-Ready Architecture
- **Microservice Design**: Distributed systems with clear separation of concerns
- **Security Best Practices**: Proper authentication, authorization, and data protection
- **Scalable Infrastructure**: Cloud-native designs with containerization support
- **Multi-Transport Support**: STDIO, SSE, and HTTP transport mechanisms for flexible deployment
- **Conversational Interfaces**: User-friendly chat interfaces for complex data interactions
- **Enterprise Authentication**: Advanced user management with bcrypt encryption, session management, and SSL/TLS support
- **LLM-Assisted Development**: Accelerated development workflows using language models to generate MCP servers, reducing development time from days to hours

### 🔧 Developer Experience
- **Comprehensive Documentation**: Detailed READMEs with setup instructions and examples
- **Interactive Notebooks**: Jupyter notebooks for learning and experimentation
- **Type Safety**: Python type hints and schema validation throughout
- **Tool Discovery**: Automatic discovery and orchestration of available capabilities
- **Chat-Based Development**: Natural language interfaces for data exploration and analysis
- **Web-Based Interfaces**: Modern, tabbed interfaces for comprehensive system management

## 🎯 Use Cases & Applications

### Healthcare & Medical
- **Medical Image Anonymization**: HIPAA-compliant processing of medical images
- **Clinical Workflow Integration**: Seamless integration with existing medical systems

### Financial Services
- **Algorithmic Trading**: Automated trading signal generation and analysis including advanced momentum strategies
- **Mean Reversion Analysis**: Connors RSI and Z-Score based strategies for overbought/oversold conditions
- **Risk Assessment**: Advanced risk metrics and portfolio analysis
- **Market Research**: Intelligent analysis of financial trends and patterns
- **Multi-Platform Access**: Financial analysis accessible through web, desktop, and API interfaces
- **Enterprise Financial Management**: Comprehensive platform combining technical analysis, CRM integration, and graph database insights

### Enterprise AI
- **Document Processing**: Automated extraction and analysis of business documents
- **Knowledge Management**: Graph-based knowledge systems for complex data relationships
- **AI-Powered Analytics**: Integration of AI capabilities into existing business workflows
- **Tool Orchestration**: Intelligent discovery and coordination of external services
- **Desktop AI Integration**: Native Claude Desktop application with MCP protocol support for enhanced productivity
- **Conversational CRM**: Chat-based interfaces for customer relationship management and data exploration
- **Full-Stack AI Platforms**: Enterprise-grade web applications with comprehensive authentication, multi-user support, and cross-system data integration

### Media & Content
- **Video Analysis**: Automated transcription, summarization, and content analysis
- **Real-Time Processing**: Live content analysis and intelligent insights

### Data Integration & Analysis
- **Cross-System Connectivity**: Seamless integration between Neo4j graph databases and HubSpot CRM
- **Natural Language Querying**: Chat-based interfaces for complex data exploration
- **Multi-Source Analytics**: Intelligent correlation and analysis across different data platforms
- **Enterprise Data Management**: Comprehensive platforms for managing and analyzing data across multiple sources with AI-powered insights

## 🚦 Getting Started

### Quick Setup
1. **Choose Your Domain**: Select a project from the table above based on your interests
2. **Follow Documentation**: Each project has comprehensive setup instructions
3. **Environment Setup**: Most projects use Python with specific dependency management
4. **API Keys**: Secure your API keys in environment variables

### Recommended Learning Path
1. **Start with RAG Systems**: Begin with the Financial Analysis RAG for foundational concepts
2. **Progress through the different trading algorithm implementations
   - Begin with basic Bollinger Z-Score analysis
   - Advance to Connors RSI for sophisticated momentum analysis
   - Explore combined strategies like Bollinger-Fibonacci
3. **Advanced Integration**: Move to MCP servers for understanding modern AI integration patterns
4. **Multi-Platform Development**: Explore the MCP client for cross-language tool orchestration
5. **LLM-Accelerated Development**: Learn how to use Claude and other LLMs to rapidly develop custom MCP servers with the comprehensive PDF processor example
6. **Conversational AI**: Set up the Chainlit MCP chatbot for natural language data interaction
7. **Enterprise Platforms**: Deploy the Streamlit CRM & Graph Platform for full-stack enterprise AI application experience
8. **Desktop AI Integration**: Set up Claude Desktop with MCP servers for native AI-tool interactions
9. **Specialized Applications**: Dive into domain-specific applications like medical AI or distributed OCR

### Research Areas
- **Multimodal AI**: Advanced integration of different AI modalities
- **Federated Learning**: Distributed machine learning implementations
- **Edge Computing**: Edge-deployed AI processing capabilities
- **Quantum Computing**: Quantum-enhanced algorithms for optimization
- **Conversational Data Science**: Natural language interfaces for complex data analysis
- **Enterprise AI Platforms**: Full-stack applications combining multiple AI services and data sources
- **Rapid MCP Development**: LLM-assisted development patterns for accelerating AI integration projects

## ⚖️ License & Disclaimer

This repository contains educational and research implementations. Individual projects may have specific licensing terms. Please review each project's documentation for:

- **Usage Rights**: Appropriate use cases and restrictions
- **API Terms**: Third-party service terms and conditions
- **Financial Disclaimer**: Investment and trading risk warnings
- **Medical Disclaimer**: Healthcare application limitations

---

**This repository represents the convergence of traditional domain expertise with cutting-edge AI capabilities, demonstrating how modern AI systems can be integrated into real-world applications while maintaining production-quality standards and best practices.**