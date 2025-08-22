"""
Dual Moving Average Crossover Strategy AI Agent with LangGraph

This script implements an intelligent trading assistant using LangGraph that analyzes stocks 
using the Dual Moving Average Crossover Strategy. The agent provides comprehensive analysis by:

1. Calculating Golden Cross (short MA above long MA) and Death Cross (short MA below long MA) signals
2. Analyzing strategy performance vs buy & hold
3. Providing detailed performance metrics (win rate, Sharpe ratio, max drawdown)
4. Generating interactive visualizations
5. Offering actionable trading recommendations

Golden Cross Strategy:
- Uses two moving averages with different periods (default: 50/200)
- Golden Cross: Short MA crosses above Long MA (bullish signal)
- Death Cross: Short MA crosses below Long MA (bearish signal)
- Supports both SMA (Simple) and EMA (Exponential) moving averages

Performance Analytics:
- Strategy vs Buy & Hold comparison
- Win rate and trade analysis
- Sharpe ratio and volatility metrics
- Maximum drawdown calculation
- Current market position assessment

Scoring System:
+80 to +100: Strong Buy (Recent Golden Cross + strong momentum)
+60 to +80: Buy (Golden Cross conditions favorable)
+40 to +60: Weak Buy (Mild bullish trend)
-40 to +40: Neutral (Hold or wait for clearer signals)
-60 to -40: Weak Sell (Mild bearish trend)
-80 to -60: Sell (Death Cross conditions)
-100 to -80: Strong Sell (Recent Death Cross + weak momentum)
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional, Tuple
from typing_extensions import TypedDict

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# Model imports - conditional based on provider
if MODEL_PROVIDER == "openai":
    from langchain_openai import ChatOpenAI
elif MODEL_PROVIDER == "vertexai":
    from langchain_google_vertexai import ChatVertexAI

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Model configuration - supports both OpenAI and Vertex AI (Gemini)
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()  # "openai" or "vertexai"

if MODEL_PROVIDER == "openai":
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("Please set the OPENAI_API_KEY environment variable in your .env file")
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
elif MODEL_PROVIDER == "vertexai":
    # Vertex AI configuration
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not GOOGLE_CLOUD_PROJECT:
        raise ValueError("Please set the GOOGLE_CLOUD_PROJECT environment variable")
    
    if GOOGLE_APPLICATION_CREDENTIALS:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS
    
    # Try to import Vertex AI dependencies
    try:
        from langchain_google_vertexai import ChatVertexAI
    except ImportError:
        raise ImportError("Please install langchain-google-vertexai: pip install langchain-google-vertexai")
else:
    raise ValueError("MODEL_PROVIDER must be either 'openai' or 'vertexai'")

# Core Dual Moving Average Strategy Functions
def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_moving_averages(data: pd.DataFrame, short_period: int, long_period: int, ma_type: str) -> Dict[str, pd.Series]:
    """Calculate both short and long moving averages"""
    close = data['Close']
    
    if ma_type.upper() == 'SMA':
        short_ma = calculate_sma(close, short_period)
        long_ma = calculate_sma(close, long_period)
    else:  # EMA
        short_ma = calculate_ema(close, short_period)
        long_ma = calculate_ema(close, long_period)
    
    return {
        'short_ma': short_ma,
        'long_ma': long_ma
    }

def generate_signals(data: pd.DataFrame, short_period: int, long_period: int, ma_type: str) -> pd.DataFrame:
    """Generate trading signals based on moving average crossovers"""
    mas = calculate_moving_averages(data, short_period, long_period, ma_type)
    
    result = data.copy()
    result[f'{ma_type}_{short_period}'] = mas['short_ma']
    result[f'{ma_type}_{long_period}'] = mas['long_ma']
    
    # Generate signals
    result['Position'] = 0
    result['Signal'] = None
    result['Cross_Type'] = None
    
    short_ma = mas['short_ma']
    long_ma = mas['long_ma']
    
    # Calculate crossovers
    short_above_long = short_ma > long_ma
    short_above_long_prev = short_above_long.shift(1)
    
    # Golden Cross: Short MA crosses above Long MA
    golden_cross = (short_above_long & ~short_above_long_prev)
    # Death Cross: Short MA crosses below Long MA  
    death_cross = (~short_above_long & short_above_long_prev)
    
    # Set signals
    result.loc[golden_cross, 'Signal'] = 'BUY'
    result.loc[golden_cross, 'Cross_Type'] = 'Golden_Cross'
    result.loc[golden_cross, 'Position'] = 1
    
    result.loc[death_cross, 'Signal'] = 'SELL'
    result.loc[death_cross, 'Cross_Type'] = 'Death_Cross'
    result.loc[death_cross, 'Position'] = -1
    
    # Forward fill positions
    result['Position'] = result['Position'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    return result

def calculate_performance_metrics(data: pd.DataFrame) -> Dict:
    """Calculate comprehensive strategy performance metrics"""
    data = data.copy()
    data['Price_Return'] = data['Close'].pct_change()
    data['Strategy_Return'] = data['Position'].shift(1) * data['Price_Return']
    data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod()
    data['Buy_Hold_Return'] = (1 + data['Price_Return']).cumprod()
    
    # Performance metrics
    total_return = data['Cumulative_Return'].iloc[-1] - 1
    buy_hold_return = data['Buy_Hold_Return'].iloc[-1] - 1
    
    # Count signals
    buy_signals = (data['Signal'] == 'BUY').sum()
    sell_signals = (data['Signal'] == 'SELL').sum()
    
    # Calculate trade-by-trade returns
    trades = data[data['Signal'].notna()].copy()
    trade_returns = []
    
    if len(trades) > 1:
        position = 0
        entry_price = 0
        
        for idx, row in trades.iterrows():
            if row['Signal'] == 'BUY' and position <= 0:
                entry_price = row['Close']
                position = 1
            elif row['Signal'] == 'SELL' and position >= 0:
                if entry_price > 0:
                    trade_return = (row['Close'] - entry_price) / entry_price
                    trade_returns.append(trade_return)
                position = -1
                entry_price = row['Close']
            elif row['Signal'] == 'BUY' and position < 0:
                if entry_price > 0:
                    trade_return = (entry_price - row['Close']) / entry_price
                    trade_returns.append(trade_return)
                position = 1
                entry_price = row['Close']
        
        win_rate = len([r for r in trade_returns if r > 0]) / len(trade_returns) if trade_returns else 0
        avg_return_per_trade = np.mean(trade_returns) if trade_returns else 0
    else:
        win_rate = 0
        avg_return_per_trade = 0
        trade_returns = []
    
    # Risk metrics
    strategy_volatility = data['Strategy_Return'].std() * np.sqrt(252)
    buy_hold_volatility = data['Price_Return'].std() * np.sqrt(252)
    
    # Sharpe ratio
    sharpe_ratio = (data['Strategy_Return'].mean() * 252) / strategy_volatility if strategy_volatility > 0 else 0
    
    # Maximum drawdown
    cumulative = data['Cumulative_Return']
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    return {
        'total_return': total_return,
        'buy_hold_return': buy_hold_return,
        'excess_return': total_return - buy_hold_return,
        'win_rate': win_rate,
        'total_trades': len(trade_returns),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'avg_return_per_trade': avg_return_per_trade,
        'strategy_volatility': strategy_volatility,
        'buy_hold_volatility': buy_hold_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown
    }

# LangGraph Tools
@tool
def analyze_dual_ma_strategy(symbol: str, period: str = "2y", short_period: int = 50, 
                           long_period: int = 200, ma_type: str = 'SMA') -> str:
    """
    Analyze a stock using the Dual Moving Average Crossover Strategy.
    
    This strategy uses two moving averages to generate trading signals:
    - Golden Cross: Short MA crosses above Long MA (Buy Signal)
    - Death Cross: Short MA crosses below Long MA (Sell Signal)
    
    Parameters:
    symbol (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    period (str): Data period (1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max)
    short_period (int): Short-term moving average period (default: 50)
    long_period (int): Long-term moving average period (default: 200)
    ma_type (str): Moving average type ('SMA' or 'EMA', default: 'SMA')
    
    Returns:
    str: Comprehensive analysis with performance metrics and current signals
    """
    
    try:
        # Download data
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            return f"Error: No data found for symbol {symbol}"
        
        # Generate signals
        data_with_signals = generate_signals(data, short_period, long_period, ma_type)
        
        # Calculate performance
        performance = calculate_performance_metrics(data_with_signals)
        
        # Get current status
        current_position = data_with_signals['Position'].iloc[-1]
        current_price = data_with_signals['Close'].iloc[-1]
        current_short_ma = data_with_signals[f'{ma_type}_{short_period}'].iloc[-1]
        current_long_ma = data_with_signals[f'{ma_type}_{long_period}'].iloc[-1]
        
        # Recent signals
        recent_signals = data_with_signals[data_with_signals['Signal'].notna()].tail(3)
        recent_signals_str = ""
        if not recent_signals.empty:
            recent_signals_str = "\nRecent Signals:\n"
            for date, row in recent_signals.iterrows():
                recent_signals_str += f"• {date.strftime('%Y-%m-%d')}: {row['Cross_Type'].replace('_', ' ')} - {row['Signal']} at ${row['Close']:.2f}\n"
        
        # Trend analysis
        trend_status = "BULLISH 🟢" if current_short_ma > current_long_ma else "BEARISH 🔴"
        trend_strength = abs(current_short_ma - current_long_ma) / current_long_ma * 100
        
        message = f"""
DUAL MOVING AVERAGE ANALYSIS - {symbol}
{'='*50}

STRATEGY PARAMETERS:
• Moving Average Type: {ma_type}
• Short Period: {short_period} days
• Long Period: {long_period} days
• Analysis Period: {period}

CURRENT STATUS:
• Current Price: ${current_price:.2f}
• {short_period}-day {ma_type}: ${current_short_ma:.2f}
• {long_period}-day {ma_type}: ${current_long_ma:.2f}
• Current Position: {'LONG' if current_position > 0 else 'SHORT' if current_position < 0 else 'NEUTRAL'}
• Trend: {trend_status}
• Trend Strength: {trend_strength:.2f}%

PERFORMANCE METRICS:
• Strategy Return: {performance['total_return']:.2%}
• Buy & Hold Return: {performance['buy_hold_return']:.2%}
• Excess Return: {performance['excess_return']:.2%}
• Win Rate: {performance['win_rate']:.2%}
• Total Trades: {performance['total_trades']}
• Sharpe Ratio: {performance['sharpe_ratio']:.3f}
• Max Drawdown: {performance['max_drawdown']:.2%}
• Strategy Volatility: {performance['strategy_volatility']:.2%}

SIGNAL SUMMARY:
• Golden Cross (Buy) Signals: {performance['buy_signals']}
• Death Cross (Sell) Signals: {performance['sell_signals']}
{recent_signals_str}

MARKET CONDITION:
{'Strong uptrend - MA separation indicates robust bullish momentum' if trend_strength > 5 and current_short_ma > current_long_ma else 
 'Moderate uptrend - MAs show bullish alignment' if trend_strength > 2 and current_short_ma > current_long_ma else
 'Weak uptrend - MAs barely bullish, watch for reversal' if current_short_ma > current_long_ma else
 'Strong downtrend - MA separation indicates robust bearish momentum' if trend_strength > 5 else
 'Moderate downtrend - MAs show bearish alignment' if trend_strength > 2 else
 'Weak downtrend - MAs barely bearish, watch for reversal'}
        """
        
        return message
        
    except Exception as e:
        return f"Error analyzing {symbol}: {str(e)}"

@tool
def calculate_dual_ma_score(symbol: str, period: str = "1y", short_period: int = 50, 
                          long_period: int = 200, ma_type: str = 'SMA') -> str:
    """
    Calculate a Dual Moving Average score between -100 and 100 for trading decisions.
    
    The score combines multiple factors:
    1. Current MA positioning (40%): Short MA vs Long MA
    2. Recent signal strength (30%): Time since last crossover and price movement
    3. Trend momentum (30%): Rate of MA separation/convergence
    
    Score Interpretation:
    +80 to +100: Strong Buy (Recent Golden Cross + strong momentum)
    +60 to +80: Buy (Golden Cross conditions favorable)  
    +40 to +60: Weak Buy (Mild bullish trend)
    -40 to +40: Neutral (Hold or wait for clearer signals)
    -60 to -40: Weak Sell (Mild bearish trend)
    -80 to -60: Sell (Death Cross conditions)
    -100 to -80: Strong Sell (Recent Death Cross + weak momentum)
    
    Parameters:
    symbol (str): Stock ticker symbol
    period (str): Data period for analysis
    short_period (int): Short MA period (default: 50)
    long_period (int): Long MA period (default: 200)
    ma_type (str): MA type ('SMA' or 'EMA')
    
    Returns:
    str: Detailed scoring analysis with recommendation
    """
    
    try:
        # Download data
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            return f"Error: No data found for symbol {symbol}"
        
        # Generate signals
        data_with_signals = generate_signals(data, short_period, long_period, ma_type)
        
        # Calculate score components
        current_short_ma = data_with_signals[f'{ma_type}_{short_period}'].iloc[-1]
        current_long_ma = data_with_signals[f'{ma_type}_{long_period}'].iloc[-1]
        current_price = data_with_signals['Close'].iloc[-1]
        
        # Component 1: MA Positioning (40% weight)
        # Positive when short MA > long MA, scaled by separation
        ma_separation = (current_short_ma - current_long_ma) / current_long_ma * 100
        positioning_score = np.clip(ma_separation * 10, -40, 40)  # Scale to ±40
        
        # Component 2: Recent Signal Strength (30% weight)  
        recent_signals = data_with_signals[data_with_signals['Signal'].notna()].tail(1)
        signal_score = 0
        
        if not recent_signals.empty:
            last_signal = recent_signals.iloc[-1]
            signal_date = recent_signals.index[-1]
            days_since_signal = (data_with_signals.index[-1] - signal_date).days
            
            # Price movement since signal
            signal_price = last_signal['Close']
            price_change = (current_price - signal_price) / signal_price * 100
            
            if last_signal['Signal'] == 'BUY':
                # Positive score if price up after buy signal
                signal_strength = price_change * (1 - min(days_since_signal / 60, 1))  # Decay over 60 days
                signal_score = np.clip(signal_strength * 3, -30, 30)
            else:  # SELL signal
                # Positive score if price down after sell signal (good for shorting)
                signal_strength = -price_change * (1 - min(days_since_signal / 60, 1))
                signal_score = np.clip(signal_strength * 3, -30, 30)
        
        # Component 3: Trend Momentum (30% weight)
        # Rate of change in MA separation
        ma_sep_series = (data_with_signals[f'{ma_type}_{short_period}'] - 
                        data_with_signals[f'{ma_type}_{long_period}']) / data_with_signals[f'{ma_type}_{long_period}'] * 100
        
        momentum = ma_sep_series.iloc[-5:].mean() - ma_sep_series.iloc[-15:-10].mean()  # 5-day vs 10-day avg
        momentum_score = np.clip(momentum * 20, -30, 30)
        
        # Combined Score
        total_score = positioning_score + signal_score + momentum_score
        total_score = np.clip(total_score, -100, 100)
        
        # Interpretation
        if total_score > 80:
            interpretation = "Strong Buy Signal"
        elif total_score > 60:
            interpretation = "Buy Signal"
        elif total_score > 40:
            interpretation = "Weak Buy Signal"
        elif total_score > -40:
            interpretation = "Neutral"
        elif total_score > -60:
            interpretation = "Weak Sell Signal"
        elif total_score > -80:
            interpretation = "Sell Signal"
        else:
            interpretation = "Strong Sell Signal"
        
        message = f"""
DUAL MOVING AVERAGE SCORE ANALYSIS - {symbol}
{'='*45}

OVERALL SCORE: {total_score:.1f}/100
SIGNAL: {interpretation}

SCORE BREAKDOWN:
• MA Positioning (40%): {positioning_score:.1f}
  └─ Separation: {ma_separation:.2f}%
• Recent Signal Strength (30%): {signal_score:.1f}
• Trend Momentum (30%): {momentum_score:.1f}

CURRENT READINGS:
• {short_period}-day {ma_type}: ${current_short_ma:.2f}
• {long_period}-day {ma_type}: ${current_long_ma:.2f}
• Current Price: ${current_price:.2f}
• Price vs Short MA: {((current_price - current_short_ma) / current_short_ma * 100):+.2f}%
• Price vs Long MA: {((current_price - current_long_ma) / current_long_ma * 100):+.2f}%

RECOMMENDATION: {interpretation}
        """
        
        return message
        
    except Exception as e:
        return f"Error calculating score for {symbol}: {str(e)}"

@tool  
def compare_ma_strategies(symbol: str, period: str = "2y") -> str:
    """
    Compare different Dual Moving Average strategy configurations for optimization.
    
    Tests multiple combinations of:
    - MA types: SMA vs EMA
    - Period combinations: (20,50), (50,200), (10,30)
    - Performance across different timeframes
    
    Parameters:
    symbol (str): Stock ticker symbol
    period (str): Data period for backtesting
    
    Returns:
    str: Comparative analysis of different MA strategy configurations
    """
    
    try:
        strategies = [
            {'short': 20, 'long': 50, 'type': 'SMA', 'name': 'Aggressive SMA 20/50'},
            {'short': 50, 'long': 200, 'type': 'SMA', 'name': 'Classic SMA 50/200'},
            {'short': 20, 'long': 50, 'type': 'EMA', 'name': 'Aggressive EMA 20/50'},
            {'short': 50, 'long': 200, 'type': 'EMA', 'name': 'Classic EMA 50/200'},
            {'short': 10, 'long': 30, 'type': 'EMA', 'name': 'Short-term EMA 10/30'}
        ]
        
        # Download data once
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            return f"Error: No data found for symbol {symbol}"
        
        results = []
        
        for strategy in strategies:
            try:
                data_with_signals = generate_signals(data, strategy['short'], strategy['long'], strategy['type'])
                performance = calculate_performance_metrics(data_with_signals)
                
                results.append({
                    'name': strategy['name'],
                    'return': performance['total_return'],
                    'excess_return': performance['excess_return'],
                    'win_rate': performance['win_rate'],
                    'sharpe': performance['sharpe_ratio'],
                    'max_dd': performance['max_drawdown'],
                    'trades': performance['total_trades']
                })
            except:
                continue
        
        if not results:
            return f"Error: Could not analyze any strategies for {symbol}"
        
        # Sort by Sharpe ratio
        results.sort(key=lambda x: x['sharpe'], reverse=True)
        
        message = f"""
DUAL MA STRATEGY COMPARISON - {symbol}
{'='*50}

RANKED BY SHARPE RATIO:

"""
        
        for i, result in enumerate(results, 1):
            message += f"""
{i}. {result['name']}
   • Total Return: {result['return']:.2%}
   • Excess Return: {result['excess_return']:.2%}
   • Win Rate: {result['win_rate']:.2%}
   • Sharpe Ratio: {result['sharpe']:.3f}
   • Max Drawdown: {result['max_dd']:.2%}
   • Total Trades: {result['trades']}
"""
        
        # Best strategy recommendation
        best = results[0]
        message += f"""

RECOMMENDATION: 
Best performing strategy is {best['name']} with:
• Sharpe Ratio: {best['sharpe']:.3f}
• Total Return: {best['return']:.2%}
• Win Rate: {best['win_rate']:.2%}

KEY INSIGHTS:
• {'EMA strategies generally more responsive but may have more whipsaws' if any('EMA' in r['name'] for r in results[:2]) else 'SMA strategies provide smoother signals'}
• {'Shorter periods generate more trades' if results[0]['trades'] > 20 else 'Longer periods provide fewer but potentially higher quality signals'}
        """
        
        return message
        
    except Exception as e:
        return f"Error comparing strategies for {symbol}: {str(e)}"

@tool
def market_scanner_dual_ma(symbols, ma_type: str = 'SMA', 
                          short_period: int = 50, long_period: int = 200) -> str:
    """
    Scan multiple symbols for Dual Moving Average signals and rank by opportunity.

    Analyzes a list of symbols and identifies the best current opportunities based on:
    - Recent crossover signals
    - Trend strength
    - Risk-reward potential

    Parameters:
    symbols: List of stock ticker symbols to analyze (can be List[str] or comma-separated string)
    ma_type (str): Moving average type ('SMA' or 'EMA')
    short_period (int): Short MA period
    long_period (int): Long MA period

    Returns:
    str: Ranked list of trading opportunities with signal analysis
    """

    # Handle both list and string inputs
    if isinstance(symbols, str):
        # Parse comma-separated string into list
        symbol_list = [s.strip().upper() for s in symbols.replace('"', '').replace("'", "").split(',')]
        symbol_list = [s for s in symbol_list if s and s.isalpha()]  # Filter valid symbols
    elif isinstance(symbols, list):
        symbol_list = [str(s).strip().upper() for s in symbols if str(s).strip()]
    else:
        return "Error: Symbols must be provided as a list or comma-separated string"

    if not symbol_list:
        return "Error: No valid symbols provided for scanning"

    # Determine appropriate data period based on long_period
    # Need at least long_period + 50 trading days for reliable calculations
    if long_period >= 200:
        data_period = "2y"  # About 500 trading days
        min_data_days = long_period + 50
    elif long_period >= 100:
        data_period = "1y"  # About 250 trading days
        min_data_days = long_period + 30
    else:
        data_period = "6mo"  # About 125 trading days
        min_data_days = long_period + 20

    print(f"🔍 Scanning symbols: {symbol_list}")
    print(f"📅 Using {data_period} data for {long_period}-day MA calculation")

    opportunities = []

    for symbol in symbol_list:
        try:
            # Get data with appropriate period
            data = yf.download(symbol, period=data_period, progress=False,
                              multi_level_index=False, auto_adjust=True)
            if data.empty:
                print(f"⚠️ No data found for {symbol}")
                continue

            # Check if we have enough data points
            if len(data) < min_data_days:
                print(f"⚠️ Insufficient data for {symbol}: {len(data)} days < {min_data_days} required")
                continue

            # Generate signals
            data_with_signals = generate_signals(data, short_period, long_period, ma_type)

            # Current status
            current_position = data_with_signals['Position'].iloc[-1]
            current_price = data_with_signals['Close'].iloc[-1]
            current_short_ma = data_with_signals[f'{ma_type}_{short_period}'].iloc[-1]
            current_long_ma = data_with_signals[f'{ma_type}_{long_period}'].iloc[-1]

            # Check for NaN values and handle them
            if pd.isna(current_short_ma) or pd.isna(current_long_ma):
                print(f"⚠️ NaN values in moving averages for {symbol} (Short MA: {current_short_ma}, Long MA: {current_long_ma})")
                # Try to get the last valid values
                short_ma_series = data_with_signals[f'{ma_type}_{short_period}'].dropna()
                long_ma_series = data_with_signals[f'{ma_type}_{long_period}'].dropna()
                
                if len(short_ma_series) == 0 or len(long_ma_series) == 0:
                    print(f"⚠️ No valid moving average data for {symbol}")
                    continue
                
                current_short_ma = short_ma_series.iloc[-1]
                current_long_ma = long_ma_series.iloc[-1]
                print(f"✅ Using last valid MAs for {symbol}: Short={current_short_ma:.2f}, Long={current_long_ma:.2f}")

            # Recent signals - only look for signals where both MAs are valid
            valid_data = data_with_signals.dropna(subset=[f'{ma_type}_{short_period}', f'{ma_type}_{long_period}'])
            recent_signals = valid_data[valid_data['Signal'].notna()].tail(1)

            signal_info = "No recent signals"
            days_since_signal = 999
            signal_type = "NONE"

            if not recent_signals.empty:
                last_signal = recent_signals.iloc[-1]
                signal_date = recent_signals.index[-1]
                days_since_signal = (data_with_signals.index[-1] - signal_date).days
                signal_type = last_signal['Signal']
                signal_info = f"{last_signal['Cross_Type'].replace('_', ' ')} {days_since_signal} days ago"

            # Trend strength - handle potential division by zero
            if current_long_ma != 0 and not pd.isna(current_long_ma):
                trend_strength = abs(current_short_ma - current_long_ma) / current_long_ma * 100
            else:
                trend_strength = 0

            trend_direction = "UP" if current_short_ma > current_long_ma else "DOWN"

            # Score based on recency and trend strength
            score = 0
            if signal_type == "BUY" and days_since_signal <= 10:
                score = (10 - days_since_signal) * 10 + trend_strength * 2
            elif signal_type == "SELL" and days_since_signal <= 10:
                score = (10 - days_since_signal) * 10 + trend_strength * 2
            else:
                score = trend_strength if trend_direction == "UP" else -trend_strength

            opportunities.append({
                'symbol': symbol,
                'score': score,
                'signal_info': signal_info,
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'current_position': current_position,
                'price': current_price,
                'days_since_signal': days_since_signal,
                'signal_type': signal_type
            })

            print(f"✅ {symbol}: Score={score:.1f}, Trend={trend_direction} ({trend_strength:.1f}%)")

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            continue

    if not opportunities:
        return f"""Error: No valid data found for any symbols in {symbol_list}

This could be due to:
- Insufficient historical data for {long_period}-day moving average
- Market data unavailable for requested symbols
- Network connectivity issues

Suggestions:
- Try using shorter MA periods (e.g., 20/50 instead of 50/200)
- Use different symbols
- Check if market is open and symbols are valid
        """

    # Sort by score (best opportunities first)
    opportunities.sort(key=lambda x: abs(x['score']), reverse=True)

    message = f"""
DUAL MA MARKET SCANNER RESULTS
{'='*40}
Strategy: {ma_type} {short_period}/{long_period}
Data Period: {data_period}
Scanned {len(symbol_list)} symbols, found {len(opportunities)} valid results

TOP OPPORTUNITIES:

"""

    for i, opp in enumerate(opportunities[:10], 1):  # Top 10
        direction_emoji = "🟢" if opp['trend_direction'] == "UP" else "🔴"
        position_text = "LONG" if opp['current_position'] > 0 else "SHORT" if opp['current_position'] < 0 else "NEUTRAL"

        message += f"""
{i}. {opp['symbol']} {direction_emoji} (Score: {opp['score']:.1f})
   • Price: ${opp['price']:.2f}
   • Position: {position_text}
   • Trend: {opp['trend_direction']} ({opp['trend_strength']:.1f}% strength)
   • Signal: {opp['signal_info']}
"""

    # Summary insights
    buy_signals = len([o for o in opportunities if o['signal_type'] == 'BUY' and o['days_since_signal'] <= 5])
    sell_signals = len([o for o in opportunities if o['signal_type'] == 'SELL' and o['days_since_signal'] <= 5])
    strong_trends = len([o for o in opportunities if o['trend_strength'] > 3])

    message += f"""

MARKET SUMMARY:
- Recent Buy Signals (≤5 days): {buy_signals}
- Recent Sell Signals (≤5 days): {sell_signals}
- Strong Trends (>3% separation): {strong_trends}
- Market Bias: {'BULLISH' if buy_signals > sell_signals else 'BEARISH' if sell_signals > buy_signals else 'MIXED'}

RECOMMENDED ACTIONS:
- Focus on symbols with recent crossovers and strong trend confirmation
- {'Consider long positions' if buy_signals > 0 else 'Consider defensive positioning'}
- Monitor trend strength for entry/exit timing
    """

    return message

# State management for LangGraph
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM based on provider
def get_llm():
    """Initialize and return the appropriate LLM based on MODEL_PROVIDER"""
    if MODEL_PROVIDER == "openai":
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    elif MODEL_PROVIDER == "vertexai":
        try:
            # Import Vertex AI enums for safety settings
            from vertexai.generative_models import HarmCategory, HarmBlockThreshold
            
            # Configure safety settings with proper enum values
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            return ChatVertexAI(
                model_name="gemini-1.5-pro-002",  # or "gemini-1.5-flash-002" for faster responses
                temperature=0.1,
                project=GOOGLE_CLOUD_PROJECT,
                max_tokens=8192,
                safety_settings=safety_settings
            )
        except ImportError:
            # Fallback without safety settings if import fails
            print("Warning: Could not import Vertex AI safety enums, using default safety settings")
            return ChatVertexAI(
                model_name="gemini-1.5-pro-002",
                temperature=0.1,
                project=GOOGLE_CLOUD_PROJECT,
                max_tokens=8192
            )
        except Exception as e:
            # Alternative approach with simpler configuration
            print(f"Warning: Safety settings configuration failed ({e}), using basic configuration")
            return ChatVertexAI(
                model_name="gemini-1.5-flash-002",  # Use flash model as fallback
                temperature=0.1,
                project=GOOGLE_CLOUD_PROJECT
            )

# Initialize LLM and tools
llm = get_llm()
tools = [
    analyze_dual_ma_strategy,
    calculate_dual_ma_score,
    compare_ma_strategies,
    market_scanner_dual_ma
]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """
    Intelligent Dual Moving Average trading chatbot that provides comprehensive analysis.
    
    The bot specializes in:
    1. Golden Cross/Death Cross signal analysis
    2. Strategy performance evaluation vs buy & hold
    3. Multi-timeframe and multi-parameter optimization
    4. Market scanning for opportunities
    5. Risk-adjusted position recommendations
    
    Dual Moving Average Strategy Overview:
    - Uses two moving averages of different periods
    - Golden Cross: Short MA crosses above Long MA (bullish)
    - Death Cross: Short MA crosses below Long MA (bearish)
    - Works best in trending markets, may whipsaw in sideways markets
    
    The classic 50/200 day combination follows the "Golden Cross" methodology
    used by institutional traders for trend identification and momentum confirmation.
    
    Supports both OpenAI GPT and Google Gemini models via Vertex AI.
    """
    
    # Filter out any non-text messages
    text_messages = [
        msg for msg in state["messages"] 
        if not (hasattr(msg, 'content') and isinstance(msg.content, list))
    ]
    
    try:
        # Get the appropriate LLM instance
        current_llm = get_llm()
        current_llm_with_tools = current_llm.bind_tools(tools)
        
        # Invoke the model
        response = current_llm_with_tools.invoke(text_messages)
        return {"messages": [response]}
        
    except Exception as e:
        print(f"Error in chatbot: {e}")
        # Fallback message
        from langchain_core.messages import AIMessage
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
        )
        return {"messages": [error_message]}

# Build the LangGraph
def create_dual_ma_agent():
    """Create and return the compiled LangGraph agent"""
    
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)
    
    # Add edges
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {"tools": "tools", "__end__": "__end__"},
    )
    
    # Compile with memory
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    
    return graph

# Main analysis function
def analyze_stock_dual_ma(symbol: str, period: str = "2y", short_period: int = 50, 
                         long_period: int = 200, ma_type: str = 'SMA', 
                         include_comparison: bool = False):
    """
    Comprehensive Dual Moving Average analysis for a stock
    
    Parameters:
    symbol (str): Stock ticker symbol
    period (str): Analysis period
    short_period (int): Short MA period  
    long_period (int): Long MA period
    ma_type (str): Moving average type
    include_comparison (bool): Whether to include strategy comparison
    
    Returns:
    str: Complete analysis results
    """
    
    graph = create_dual_ma_agent()
    config = {"configurable": {"thread_id": "dual_ma_analysis"}}
    
    analysis_request = f"""
    Please provide a comprehensive Dual Moving Average analysis for {symbol} with the following requirements:
    
    1. **Strategy Analysis**: Use analyze_dual_ma_strategy with parameters:
       - Symbol: {symbol}
       - Period: {period}
       - Short Period: {short_period}
       - Long Period: {long_period}
       - MA Type: {ma_type}
    
    2. **Scoring Analysis**: Calculate dual_ma_score to get a trading recommendation
    
    {f"3. **Strategy Comparison**: Compare different MA configurations to identify optimal parameters" if include_comparison else ""}
    
    4. **Final Recommendation**: Based on all analyses, provide:
       - Clear BUY/SELL/HOLD recommendation
       - Risk level assessment
       - Entry/exit strategy suggestions
       - Stop-loss recommendations
    
    Please provide detailed reasoning for your final recommendation.
    """
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=analysis_request)]},
        config
    )
    
    return result["messages"][-1].content

def scan_market_opportunities(symbols: List[str], ma_type: str = 'SMA', 
                            short_period: int = 50, long_period: int = 200):
    """
    Scan multiple symbols for Dual MA trading opportunities
    
    Parameters:
    symbols (List[str]): List of stock symbols to scan
    ma_type (str): Moving average type
    short_period (int): Short MA period
    long_period (int): Long MA period
    
    Returns:
    str: Market scan results with ranked opportunities
    """
    
    graph = create_dual_ma_agent()
    config = {"configurable": {"thread_id": "market_scanner"}}
    
    scan_request = f"""
    Please scan the market for Dual Moving Average trading opportunities using:
    
    1. **Market Scanner**: Use market_scanner_dual_ma with:
       - Symbols: {symbols}
       - MA Type: {ma_type}
       - Short Period: {short_period}
       - Long Period: {long_period}
    
    2. **Top Picks Analysis**: For the top 3 opportunities, provide detailed analysis including:
       - Recent signal strength
       - Trend confirmation
       - Risk assessment
       - Recommended position size
    
    3. **Market Overview**: Summarize current market conditions and sector trends
    
    Focus on actionable insights and clear next steps for traders.
    """
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=scan_request)]},
        config
    )
    
    return result["messages"][-1].content

# Example usage and testing functions
def main():
    """Main function demonstrating the Dual MA AI Agent capabilities"""
    
    print("🤖 Dual Moving Average AI Trading Agent")
    print(f"🔧 Using {MODEL_PROVIDER.upper()} as LLM provider")
    print("=" * 50)
    
    # Display model information
    if MODEL_PROVIDER == "openai":
        print("📡 Model: GPT-4o-mini via OpenAI")
    elif MODEL_PROVIDER == "vertexai":
        print(f"📡 Model: Gemini via Vertex AI (Project: {GOOGLE_CLOUD_PROJECT})")
    
    print()
    
    # Example 1: Single stock analysis
    print("\n📊 ANALYZING APPLE (AAPL)")
    print("-" * 30)
    
    try:
        result = analyze_stock_dual_ma(
            symbol="AAPL",
            period="2y",
            short_period=50,
            long_period=200,
            ma_type='SMA',
            include_comparison=True
        )
        print(result)
    except Exception as e:
        print(f"Error analyzing AAPL: {e}")
    
    print("\n" + "=" * 50)
    
    # Example 2: Market scanner
    print("\n🔍 MARKET SCANNER - TECH STOCKS")
    print("-" * 35)
    
    tech_stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX"]
    
    try:
        scanner_result = scan_market_opportunities(
            symbols=tech_stocks,
            ma_type='EMA',
            short_period=20,
            long_period=50
        )
        print(scanner_result)
    except Exception as e:
        print(f"Error scanning market: {e}")
    
    print("\n" + "=" * 50)
    
    # Example 3: Interactive mode
    print("\n💬 INTERACTIVE MODE")
    print("-" * 20)
    print("Enter 'quit' to exit, or ask questions about Dual MA strategy...")
    print(f"Powered by {MODEL_PROVIDER.upper()}")
    
    graph = create_dual_ma_agent()
    config = {"configurable": {"thread_id": "interactive_session"}}
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye! Happy trading!")
                break
            
            if not user_input:
                continue
            
            result = graph.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config
            )
            
            print(f"\n🤖 AI Agent: {result['messages'][-1].content}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Happy trading!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def test_model_connection():
    """Test the model connection and basic functionality"""
    print(f"🧪 Testing {MODEL_PROVIDER.upper()} connection...")
    
    try:
        llm = get_llm()
        
        # Simple test message
        test_message = "Hello! Please respond with 'Connection successful' if you can read this."
        response = llm.invoke(test_message)
        
        print(f"✅ {MODEL_PROVIDER.upper()} connection successful!")
        print(f"📝 Model response: {response.content[:100]}...")
        
        # Test with a simple trading question
        trading_test = "What is a golden cross in trading? Please keep your answer brief."
        trading_response = llm.invoke(trading_test)
        print(f"📈 Trading knowledge test: {trading_response.content[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ {MODEL_PROVIDER.upper()} connection failed: {e}")
        
        # Additional debugging info for Vertex AI
        if MODEL_PROVIDER == "vertexai":
            print("\n🔍 Vertex AI Debugging Info:")
            print(f"   Project: {GOOGLE_CLOUD_PROJECT}")
            print(f"   Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Using default credentials')}")
            
            # Test basic Google Cloud authentication
            try:
                import google.auth
                credentials, project = google.auth.default()
                print(f"   Auth Project: {project}")
                print("   ✅ Google Cloud authentication working")
            except Exception as auth_error:
                print(f"   ❌ Google Cloud authentication failed: {auth_error}")
                print("   💡 Try: gcloud auth application-default login")
        
        elif MODEL_PROVIDER == "openai":
            print("\n🔍 OpenAI Debugging Info:")
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key:
                print(f"   API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]} (length: {len(api_key)})")
            else:
                print("   ❌ No API key found")
        
        return False

def get_simple_vertex_ai_llm():
    """Get a simplified Vertex AI LLM without safety settings"""
    return ChatVertexAI(
        model_name="gemini-1.5-flash-002",
        temperature=0.1,
        project=GOOGLE_CLOUD_PROJECT
    )

def test_vertex_ai_models():
    """Test different Vertex AI model configurations"""
    models_to_test = [
        "gemini-1.5-pro-002",
        "gemini-1.5-flash-002", 
        "gemini-1.0-pro-002"
    ]
    
    print("🧪 Testing different Vertex AI models...")
    
    for model in models_to_test:
        try:
            llm = ChatVertexAI(
                model_name=model,
                temperature=0.1,
                project=GOOGLE_CLOUD_PROJECT
            )
            response = llm.invoke("Hello")
            print(f"✅ {model}: Working")
            return llm
        except Exception as e:
            print(f"❌ {model}: Failed ({str(e)[:50]}...)")
    
    return None

def switch_model_provider(new_provider: str):
    """
    Switch between OpenAI and Vertex AI providers
    
    Parameters:
    new_provider (str): Either "openai" or "vertexai"
    """
    global MODEL_PROVIDER, llm, llm_with_tools
    
    if new_provider.lower() not in ["openai", "vertexai"]:
        print("❌ Invalid provider. Use 'openai' or 'vertexai'")
        return False
    
    MODEL_PROVIDER = new_provider.lower()
    os.environ["MODEL_PROVIDER"] = MODEL_PROVIDER
    
    try:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        print(f"✅ Switched to {MODEL_PROVIDER.upper()}")
        return test_model_connection()
    except Exception as e:
        print(f"❌ Failed to switch to {MODEL_PROVIDER.upper()}: {e}")
        return False

if __name__ == "__main__":
    # Test model connection first
    if test_model_connection():
        main()
    else:
        print("\n📋 Setup Instructions:")
        print("-" * 20)
        
        if MODEL_PROVIDER == "openai":
            print("For OpenAI:")
            print("1. Set OPENAI_API_KEY in your .env file")
            print("2. Install: pip install langchain-openai")
        
        elif MODEL_PROVIDER == "vertexai":
            print("For Vertex AI (Gemini):")
            print("1. Set GOOGLE_CLOUD_PROJECT in your .env file")
            print("2. Set up authentication:")
            print("   - Service Account: Set GOOGLE_APPLICATION_CREDENTIALS")
            print("   - Or use: gcloud auth application-default login")
            print("3. Install required packages:")
            print("   pip install langchain-google-vertexai google-cloud-aiplatform")
            print("4. Enable Vertex AI API in your Google Cloud project:")
            print("   gcloud services enable aiplatform.googleapis.com")
            print("5. Check your authentication:")
            print("   gcloud auth list")
            print("   gcloud config get-value project")
            
            # Offer to test different models
            print("\n🔧 Troubleshooting:")
            test_choice = input("Would you like to test different Vertex AI models? (y/n): ").lower()
            if test_choice in ['y', 'yes']:
                working_model = test_vertex_ai_models()
                if working_model:
                    print("✅ Found a working model! You can now use the system.")
        
        print("\n🔄 You can also switch providers by setting MODEL_PROVIDER=openai or MODEL_PROVIDER=vertexai in your .env file")