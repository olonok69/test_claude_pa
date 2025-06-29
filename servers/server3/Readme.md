# Yahoo Finance MCP Server

A Model Context Protocol (MCP) server that provides comprehensive financial data analysis and technical indicators through Yahoo Finance integration. This server enables AI assistants and applications to access real-time market data, perform technical analysis, and generate trading signals with advanced proprietary scoring algorithms.

## 🚀 Features

- **Real-time Market Data**: Access current stock prices, trading volumes, and market information
- **Technical Analysis Tools**: Advanced indicators including MACD, Bollinger Bands, Donchian Channels
- **Custom Scoring Systems**: Proprietary algorithms for combined technical analysis
- **Trading Signal Generation**: Automated buy/sell/hold recommendations
- **Portfolio Analysis**: Multi-indicator scoring for investment decisions
- **MCP Compatible**: Implements the Model Context Protocol for AI assistant integration

## 📋 Prerequisites

- Python 3.12+
- Docker (optional, for containerized deployment)
- Internet connection for Yahoo Finance data access
- No API keys required (uses public Yahoo Finance data)

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository and navigate to the server directory**:
   ```bash
   cd servers/server3
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build the Docker image**:
   ```bash
   docker build -t yahoo-finance-mcp-server .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8002:8002 yahoo-finance-mcp-server
   ```

## 🎯 Available Tools

The server provides 6 powerful financial analysis tools:

### 1. `calculate-macd-score-tool`
**MACD Technical Analysis with Custom Scoring**

- **Purpose**: Calculates a comprehensive MACD score (-100 to +100) combining three components
- **Components**:
  - MACD line vs Signal line position (40% weight)
  - MACD line vs Zero line position (30% weight)
  - Histogram momentum analysis (30% weight)
- **Parameters**:
  - `symbol`: Stock ticker (e.g., "AAPL", "TSLA")
  - `period`: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
  - `fast_period`: Fast EMA period (default: 12)
  - `slow_period`: Slow EMA period (default: 26)
  - `signal_period`: Signal line EMA period (default: 9)

### 2. `calculate-donchian-channel-score-tool`
**Donchian Channel Analysis with Custom Scoring**

- **Purpose**: Calculates Donchian Channel score (-100 to +100) for trend and volatility analysis
- **Components**:
  - Price position within channel (50% weight)
  - Channel direction trend (30% weight)
  - Channel width trend analysis (20% weight)
- **Parameters**:
  - `symbol`: Stock ticker
  - `period`: Time period
  - `window`: Lookback period for channel calculation (default: 20)

### 3. `calculate-combined-score-macd-donchian`
**Multi-Indicator Combined Analysis**

- **Purpose**: Combines MACD and Donchian scores for comprehensive trading signals
- **Trading Signals**:
  - +75 to +100: Strong Buy
  - +50 to +75: Buy
  - +25 to +50: Weak Buy
  - -25 to +25: Neutral (Hold)
  - -50 to -25: Weak Sell
  - -75 to -50: Sell
  - -100 to -75: Strong Sell
- **Parameters**: Combines all MACD and Donchian parameters

### 4. `calculate-bollinger-fibonacci-score`
**Advanced Bollinger Bands + Fibonacci Retracement Strategy**

- **Purpose**: Sophisticated trading strategy combining Bollinger Bands with Fibonacci levels
- **Score Components**:
  - Bollinger Band position (30% weight)
  - Volatility assessment (15% weight)
  - Fibonacci level interaction (35% weight)
  - Price momentum analysis (20% weight)
- **Parameters**:
  - `ticker`: Stock ticker
  - `period`: Time period
  - `window`: Bollinger Bands period (default: 20)
  - `num_std`: Standard deviations for bands (default: 2)
  - `window_swing_points`: Swing point detection period (default: 10)
  - `fibonacci_levels`: Fibonacci retracement levels
  - `num_days`: Number of recent days to analyze (default: 3)

### 5. `calculate-bollinger-z-score`
**Bollinger Z-Score Analysis**

- **Purpose**: Calculates normalized position relative to Bollinger Bands
- **Interpretation**:
  - Z-Score > +2: Overbought (potential sell signal)
  - Z-Score < -2: Oversold (potential buy signal)
  - Z-Score between -2 and +2: Normal trading range
- **Parameters**:
  - `symbol`: Stock ticker
  - `period`: Calculation period (default: 20)

### 6. `calculate-connors-rsi-score-tool` (Utility Function)
**Connors RSI Analysis**

- **Purpose**: Advanced RSI calculation combining price RSI, streak RSI, and percent rank
- **Components**:
  - Price RSI (33.33% weight)
  - Streak RSI (33.33% weight)
  - Percent Rank (33.33% weight)

## 📊 Usage Examples

### Basic Technical Analysis
```python
# Get MACD analysis for Apple stock
{
  "symbol": "AAPL",
  "period": "1y",
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9
}
```

### Combined Trading Signal
```python
# Get comprehensive trading signal for Tesla
{
  "symbol": "TSLA",
  "period": "6mo",
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9,
  "window": 20
}
```

### Advanced Strategy Analysis
```python
# Bollinger-Fibonacci strategy for Microsoft
{
  "ticker": "MSFT",
  "period": "1y",
  "window": 20,
  "num_std": 2,
  "window_swing_points": 10,
  "fibonacci_levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
  "num_days": 5
}
```

## 🔧 API Endpoints

### MCP Tools

The server exposes financial analysis tools through the MCP protocol:

- **Tool Discovery**: Automatic registration of all available analysis tools
- **Schema Validation**: Comprehensive input validation using Zod schemas
- **Error Handling**: Robust error management with detailed feedback

### HTTP Endpoints

- **Health Check**: `GET /health` - Verify server status
- **SSE Endpoint**: `GET /sse` - Server-Sent Events for MCP communication
- **Message Handler**: `POST /messages/` - Handle MCP protocol messages

## 🏗️ Architecture

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client      │    │   FastAPI        │    │   Yahoo Finance │
│                   │◄──►│   Server         │◄──►│   API           │
│  - Tool Requests  │    │  - Tool Registry │    │  - Market Data  │
│  - Result Display │    │  - SSE Transport │    │  - Historical   │
│  - Error Handling │    │  - Validation    │    │    Data         │
└───────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

- **`main.py`**: FastAPI server with SSE transport implementation
- **`utils/yahoo_finance_tools.py`**: Core financial analysis algorithms
- **Tool Registration**: Auto-discovery and MCP tool registration system
- **Validation Layer**: Zod-based input validation for all tools

## 🧮 Technical Indicators Deep Dive

### MACD Scoring Algorithm

The MACD score combines three weighted components:

1. **Signal Line Crossing (40%)**:
   - Measures MACD line position relative to signal line
   - Normalized using 3-sigma range for consistency

2. **Zero Line Analysis (30%)**:
   - Evaluates MACD line position relative to zero
   - Indicates overall trend strength

3. **Histogram Momentum (30%)**:
   - Analyzes rate of change in MACD histogram
   - Captures acceleration/deceleration patterns

### Donchian Channel Scoring

The Donchian score evaluates three aspects:

1. **Channel Position (50%)**:
   - Price location within the channel bounds
   - Linear scaling from lower band (-50) to upper band (+50)

2. **Channel Direction (30%)**:
   - Trend analysis of the channel midpoint
   - 5-day smoothed directional change

3. **Volatility Assessment (20%)**:
   - Channel width expansion/contraction analysis
   - Indicates market volatility changes

### Bollinger-Fibonacci Integration

Advanced strategy combining:

1. **%B Position**: Bollinger Band percentage position
2. **Volatility Metrics**: Band width and expansion analysis
3. **Fibonacci Interactions**: Price proximity to key retracement levels
4. **Momentum Indicators**: RSI-based momentum assessment

## 🔍 Error Handling

The server includes comprehensive error handling:

- **Data Validation**: Input parameter validation and type checking
- **API Errors**: Yahoo Finance API error management and retry logic
- **Calculation Errors**: Mathematical operation error handling
- **Missing Data**: Graceful handling of insufficient historical data

## 📈 Performance Considerations

- **Data Caching**: Efficient caching of frequently requested symbols
- **Batch Processing**: Optimized calculations for multiple indicators
- **Memory Management**: Efficient pandas DataFrame operations
- **API Rate Limiting**: Respectful Yahoo Finance API usage

## 🐛 Troubleshooting

### Common Issues

**Symbol Not Found**:
- Verify ticker symbol format (e.g., "AAPL" not "Apple")
- Check if symbol exists on Yahoo Finance
- Use correct exchange suffixes for international stocks

**Insufficient Data**:
- Reduce analysis period requirements
- Check if symbol has sufficient trading history
- Verify market hours and data availability

**Calculation Errors**:
- Ensure minimum data requirements are met
- Check for corporate actions affecting price data
- Verify parameter ranges are within valid bounds

### Debug Mode

Enable detailed logging by setting log level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔗 Integration with AI Assistants

This server implements the Model Context Protocol (MCP), making it compatible with:
- Claude Desktop
- Other MCP-compatible AI assistants
- Custom applications using MCP clients

### MCP Client Configuration

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "yahoo-finance": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/servers/server3"
    }
  }
}
```

## 💡 Use Cases

### Portfolio Management
- Analyze multiple stocks simultaneously
- Generate combined technical signals
- Track momentum across different timeframes

### Trading Strategy Development
- Backtest indicator combinations
- Evaluate signal accuracy and timing
- Develop custom scoring methodologies

### Market Research
- Sector analysis using multiple indicators
- Comparative technical analysis
- Trend identification and validation

### Educational Applications
- Learn technical analysis concepts
- Understand indicator interactions
- Practice signal interpretation

## 🔄 Future Enhancements

- **Additional Indicators**: RSI, Stochastic, Williams %R
- **Sector Analysis**: Industry-wide technical analysis
- **Options Data**: Volatility and options flow analysis
- **Economic Indicators**: Integration with economic data
- **Real-time Streaming**: Live market data updates

---

**Version**: 1.0.0  
**Compatible with**: Python 3.12+, FastAPI 0.104+, MCP 1.6.0+, yfinance 0.2.61+